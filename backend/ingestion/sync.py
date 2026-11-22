"""Pull matches from PandaScore and upsert them into the database.

Usage:
    python -m ingestion.sync
    python -m ingestion.sync --loop --interval 60
"""

import argparse
import logging
import time
from datetime import UTC, datetime, timedelta

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import Base, SessionLocal, engine
from app.models import Game, Match, Player, Team
from ingestion.pandascore_client import MAX_PAGE_SIZE, STATUSES, PandaScoreClient

log = logging.getLogger("ingestion")


def parse_dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


def parse_match(payload: dict) -> tuple[dict, list[dict]]:
    """Convert a PandaScore match payload into (match_fields, team_fields)."""
    opponents = [o["opponent"] for o in payload.get("opponents", []) if o.get("opponent")]
    scores = {r["team_id"]: r.get("score") for r in payload.get("results", [])}
    team1 = opponents[0] if len(opponents) > 0 else None
    team2 = opponents[1] if len(opponents) > 1 else None

    match = {
        "id": payload["id"],
        "videogame": (payload.get("videogame") or {}).get("slug", "unknown"),
        "name": payload.get("name") or "TBD",
        "status": payload["status"],
        "league_name": (payload.get("league") or {}).get("name"),
        "tournament_name": (payload.get("tournament") or {}).get("name"),
        "scheduled_at": parse_dt(payload.get("scheduled_at")),
        "begin_at": parse_dt(payload.get("begin_at")),
        "end_at": parse_dt(payload.get("end_at")),
        "number_of_games": payload.get("number_of_games"),
        "match_type": payload.get("match_type"),
        "team1_id": team1["id"] if team1 else None,
        "team2_id": team2["id"] if team2 else None,
        "team1_score": scores.get(team1["id"]) if team1 else None,
        "team2_score": scores.get(team2["id"]) if team2 else None,
        "winner_id": payload.get("winner_id"),
        "stream_url": pick_stream(payload.get("streams_list") or []),
    }
    teams = [
        {k: t.get(k) for k in ("id", "name", "acronym", "image_url")} for t in (team1, team2) if t
    ]
    return match, teams


def pick_stream(streams: list[dict]) -> str | None:
    """Main stream first, then any official one, then whatever is listed."""
    for wanted in ("main", "official", None):
        for stream in streams:
            if (wanted is None or stream.get(wanted)) and stream.get("raw_url"):
                return stream["raw_url"]
    return None


def parse_games(payload: dict) -> list[dict]:
    return [
        {
            "id": g["id"],
            "match_id": payload["id"],
            "position": g["position"],
            "status": g["status"],
            "winner_id": (g.get("winner") or {}).get("id"),
            "length": g.get("length"),
        }
        for g in payload.get("games") or []
    ]


def is_team_match(payload: dict) -> bool:
    """Some games (e.g. StarCraft 2) are player vs player; only team matches are stored."""
    return all(o.get("type", "Team") == "Team" for o in payload.get("opponents", []))


def upsert_match(session: Session, payload: dict) -> None:
    match, teams = parse_match(payload)
    for team in teams:
        session.merge(Team(**team))
    session.flush()  # teams must exist before the match references them
    session.merge(Match(**match))
    session.flush()  # the match must exist before its games reference it
    for game in parse_games(payload):
        session.merge(Game(**game))


def parse_player(payload: dict, team_id: int) -> dict:
    fields = ("id", "name", "first_name", "last_name", "role", "nationality", "image_url")
    player = {k: payload.get(k) for k in fields}
    player["first_name"] = (player["first_name"] or "").strip() or None
    player["last_name"] = (player["last_name"] or "").strip() or None
    player["team_id"] = team_id
    return player


def refresh_rosters(
    session: Session,
    client: PandaScoreClient,
    max_age: timedelta = timedelta(hours=24),
    now: datetime | None = None,
) -> int:
    """Refresh the rosters of the stalest teams, at most one API request per call."""
    now = now or datetime.now(UTC)
    stale = session.scalars(
        select(Team)
        .where(or_(Team.roster_synced_at.is_(None), Team.roster_synced_at < now - max_age))
        .order_by(Team.roster_synced_at.is_not(None), Team.roster_synced_at)
        .limit(MAX_PAGE_SIZE)
    ).all()
    if not stale:
        return 0
    rosters = {t["id"]: t.get("players") or [] for t in client.teams([t.id for t in stale])}
    for team in stale:
        players = rosters.get(team.id, [])
        keep = {p["id"] for p in players}
        for old in team.players:
            if old.id not in keep:
                old.team_id = None  # left the team
        for p in players:
            session.merge(Player(**parse_player(p, team.id)))
        # Also stamp teams missing from the response, so they are not retried every cycle.
        team.roster_synced_at = now
    session.commit()
    log.info("refreshed rosters of %d teams", len(stale))
    return len(stale)


def sync_once(
    session: Session,
    client: PandaScoreClient,
    statuses: tuple[str, ...] = STATUSES,
    per_page: int = 50,
) -> int:
    count = skipped = 0
    for status in statuses:
        for payload in client.matches(status, per_page=per_page):
            if not is_team_match(payload):
                skipped += 1
                continue
            upsert_match(session, payload)
            count += 1
    session.commit()
    log.info("synced %d matches, skipped %d player matches", count, skipped)
    refresh_rosters(session, client)
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync esports matches from PandaScore")
    parser.add_argument("--loop", action="store_true", help="run forever")
    parser.add_argument("--interval", type=int, default=60, help="seconds between runs")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = get_settings()
    Base.metadata.create_all(engine)

    with PandaScoreClient(settings.pandascore_token, settings.pandascore_base_url) as client:
        while True:
            try:
                with SessionLocal() as session:
                    sync_once(session, client)
            except Exception:
                log.exception("sync failed")
                if not args.loop:
                    raise
            if not args.loop:
                break
            time.sleep(args.interval)


if __name__ == "__main__":
    main()
