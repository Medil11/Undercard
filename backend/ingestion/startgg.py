"""Fighting games from start.gg (GraphQL), stored next to PandaScore data.

start.gg ids are stored negated so they never collide with PandaScore ids, and rows carry
source="startgg". Only notable events are kept: at least MIN_ENTRANTS entrants or a start.gg
staff pick with at least MIN_PICK_ENTRANTS, and only their final bracket phases
(one group, 64 seeds or fewer).

Real payload facts (checked against the API):
- `Set.totalGames` is the series length; `bestOf` can disagree with the actual score.
- Status comes from `startedAt` / `completedAt`, not from the numeric `state`.
- Future sets often have no entrants yet; they are skipped until both are known.
- `Game` has no duration.
"""

import logging
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy.orm import Session

from ingestion.store import save_match

log = logging.getLogger("ingestion")

API_URL = "https://api.start.gg/gql/alpha"
# start.gg videogame id -> our slug (see GAMES in frontend/index.html for display names)
VIDEOGAMES = {
    43868: "sf6",
    49783: "tekken-8",
    1386: "ssbu",
    1: "ssbm",
    33945: "ggst",
    48599: "mk1",
    64423: "2xko",
    73221: "fatal-fury",
}
MIN_ENTRANTS = 100
MIN_PICK_ENTRANTS = 32  # side brackets of a staff-picked tournament are noise
WINDOW_BEFORE, WINDOW_AFTER = timedelta(days=2), timedelta(days=4)
DISCOVERY_EVERY = timedelta(minutes=30)
LEAD_TIME = timedelta(hours=2)  # events further away than this are not polled every minute
MAX_FINAL_SEEDS = 64
SETS_PER_PAGE, MAX_SET_PAGES = (
    30,
    5,
)  # 40 sets with players and images cost 1,081 objects; the cap is 1,000

# start.gg treats staffPicks:null like true, so the filter is written in or left out entirely.
TOURNAMENTS_QUERY = """
query($ids:[ID],$after:Timestamp,$before:Timestamp,$page:Int){
  tournaments(query:{perPage:40,page:$page,sortBy:"startAt asc",
    filter:{videogameIds:$ids,afterDate:$after,beforeDate:$before%s}}){
    pageInfo{totalPages}
    nodes{id name events(filter:{videogameId:$ids}){
      id name numEntrants state startAt videogame{id}}}
  }
}"""
PHASES_QUERY = "query($id:ID){event(id:$id){phases{id name numSeeds groupCount}}}"
SETS_QUERY = """
query($id:ID,$phases:[ID],$page:Int,$per:Int){event(id:$id){sets(page:$page,perPage:$per,
  sortType:RECENT,filters:{phaseIds:$phases}){
  pageInfo{totalPages}
  nodes{id bestOf totalGames fullRoundText startAt startedAt completedAt winnerId
    phaseGroup{phase{name}}
    stream{streamName streamSource}
    games{id orderNum winnerId}
    slots{entrant{id name participants{gamerTag prefix user{images(type:"profile"){url}}}}
      standing{stats{score{value}}}}}
}}}"""


class StartggClient:
    def __init__(self, token: str, transport: httpx.BaseTransport | None = None) -> None:
        self._http = httpx.Client(
            headers={"Authorization": f"Bearer {token}"}, timeout=30.0, transport=transport
        )

    def query(self, query: str, variables: dict) -> dict:
        response = self._http.post(API_URL, json={"query": query, "variables": variables})
        response.raise_for_status()
        body = response.json()
        if body.get("errors") or body.get("data") is None:
            raise RuntimeError(f"start.gg error: {str(body.get('errors') or body)[:300]}")
        return body["data"]

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "StartggClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


# Discovery is costly (one request per 40 tournaments), so it runs every 30 minutes and is
# kept in memory. Completed events are synced once more, then skipped.
_cache: dict = {"at": None, "events": [], "done": set()}


def _ts(value: int | None) -> datetime | None:
    return datetime.fromtimestamp(value, UTC) if value else None


def discover(client: StartggClient, now: datetime) -> list[dict]:
    """Notable events of the tracked games around now, with their final phases."""
    variables = {
        "ids": list(VIDEOGAMES),
        "after": int((now - WINDOW_BEFORE).timestamp()),
        "before": int((now + WINDOW_AFTER).timestamp()),
    }
    candidates: dict[int, dict] = {}
    for picks in (True, False):  # staff picks first, then everything (sized by entrants)
        query = TOURNAMENTS_QUERY % (",staffPicks:true" if picks else "")
        page, pages = 1, 1
        while page <= pages:
            data = client.query(query, {**variables, "page": page})
            pages = data["tournaments"]["pageInfo"]["totalPages"] or 1
            for tournament in data["tournaments"]["nodes"] or []:
                for event in tournament["events"] or []:
                    game = VIDEOGAMES.get(int((event.get("videogame") or {}).get("id") or 0))
                    size = event.get("numEntrants") or 0
                    if game and size >= (MIN_PICK_ENTRANTS if picks else MIN_ENTRANTS):
                        candidates[int(event["id"])] = {
                            "id": int(event["id"]),
                            "tournament": tournament["name"],
                            "videogame": game,
                            "state": event.get("state"),
                            "start": _ts(event.get("startAt")),
                        }
            page += 1
    events = []
    for event in candidates.values():
        phases = client.query(PHASES_QUERY, {"id": event["id"]})["event"]["phases"] or []
        finals = [
            p
            for p in phases
            if p.get("groupCount") == 1 and (p.get("numSeeds") or 0) <= MAX_FINAL_SEEDS
        ]
        if finals:
            events.append({**event, "phases": [int(p["id"]) for p in finals]})
    log.info("start.gg: %d notable events out of %d candidates", len(events), len(candidates))
    return events


def stream_url(stream: dict | None) -> str | None:
    if stream and stream.get("streamSource") == "TWITCH" and stream.get("streamName"):
        return f"https://www.twitch.tv/{stream['streamName']}"
    return None


def parse_entrant(entrant: dict) -> dict:
    participant = (entrant.get("participants") or [{}])[0]
    images = ((participant.get("user") or {}).get("images")) or []
    return {
        "id": -int(entrant["id"]),
        "name": participant.get("gamerTag") or entrant["name"],
        "acronym": None,
        "image_url": images[0]["url"] if images else None,
        "source": "startgg",
    }


def parse_set(payload: dict, event: dict) -> tuple[dict, list[dict], list[dict]] | None:
    """Convert a start.gg set into (match, players as teams, games), or None if incomplete."""
    try:
        set_id = int(payload["id"])  # preview sets have string ids
    except (TypeError, ValueError):
        return None
    slots = payload.get("slots") or []
    entrants = [s.get("entrant") for s in slots]
    if len(entrants) != 2 or not all(entrants):
        return None
    players = [parse_entrant(e) for e in entrants]
    scores = [
        (((s.get("standing") or {}).get("stats") or {}).get("score") or {}).get("value")
        for s in slots
    ]
    started, completed = _ts(payload.get("startedAt")), _ts(payload.get("completedAt"))
    status = "finished" if completed else "running" if started else "not_started"
    scored = status != "not_started"

    def score(value: float | None) -> int | None:
        return max(int(value), 0) if scored and value is not None else None

    round_text = payload.get("fullRoundText") or "Match"
    phase = ((payload.get("phaseGroup") or {}).get("phase") or {}).get("name")
    match = {
        "id": -set_id,
        "source": "startgg",
        "videogame": event["videogame"],
        "name": f"{round_text}: {players[0]['name']} vs {players[1]['name']}",
        "status": status,
        "league_name": event["tournament"],
        "tournament_name": phase or round_text,
        "scheduled_at": _ts(payload.get("startAt")) or started or completed,
        "begin_at": started,
        "end_at": completed,
        "number_of_games": payload.get("totalGames") or payload.get("bestOf"),
        "match_type": "best_of",
        "team1_id": players[0]["id"],
        "team2_id": players[1]["id"],
        "team1_score": score(scores[0]),
        "team2_score": score(scores[1]),
        "winner_id": -int(payload["winnerId"]) if payload.get("winnerId") else None,
        "stream_url": stream_url(payload.get("stream")),
    }
    games = [
        {
            "id": -int(g["id"]),
            "match_id": -set_id,
            "position": g["orderNum"],
            "status": "finished" if g.get("winnerId") else "not_started",
            "winner_id": -int(g["winnerId"]) if g.get("winnerId") else None,
            "length": None,
        }
        for g in payload.get("games") or []
        if g.get("id") and g.get("orderNum")
    ]
    return match, players, games


def sync_startgg(
    session: Session, client: StartggClient, now: datetime | None = None, cache: dict | None = None
) -> int:
    """Upsert the final-bracket sets of notable fighting game events. Returns the set count."""
    now = now or datetime.now(UTC)
    cache = _cache if cache is None else cache
    if cache["at"] is None or now - cache["at"] >= DISCOVERY_EVERY:
        cache["events"], cache["at"] = discover(client, now), now
    count = 0
    for event in cache["events"]:
        if event["id"] in cache["done"]:
            continue
        if (
            event.get("state") == "CREATED"
            and event.get("start")
            and event["start"] > now + LEAD_TIME
        ):
            continue
        page, pages = 1, 1
        while page <= min(pages, MAX_SET_PAGES):
            data = client.query(
                SETS_QUERY,
                {"id": event["id"], "phases": event["phases"], "page": page, "per": SETS_PER_PAGE},
            )
            sets = data["event"]["sets"]
            pages = sets["pageInfo"]["totalPages"] or 1
            for payload in sets["nodes"] or []:
                parsed = parse_set(payload, event)
                if parsed is None:
                    continue
                match, players, games = parsed
                save_match(session, match, players, games)
                count += 1
            page += 1
        # Unplayed sets (a bracket reset) stay open forever, so trust the event state instead.
        if event.get("state") == "COMPLETED":
            cache["done"].add(event["id"])
    session.commit()
    log.info("start.gg: synced %d sets", count)
    return count
