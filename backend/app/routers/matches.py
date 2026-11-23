import logging
import time
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.config import get_settings
from app.db import get_db
from app.models import Match, Player, Team
from app.schemas import (
    BracketMatch,
    LeagueOut,
    MatchDetailOut,
    MatchOut,
    PlayerDetailOut,
    StandingOut,
    TeamDetailOut,
    TeamSuggestion,
    VideogameOut,
)
from ingestion.pandascore_client import PandaScoreClient

router = APIRouter(tags=["matches"])
log = logging.getLogger("api")
STANDINGS_TTL = 600  # seconds; fetched on demand, so each tournament costs at most 6 requests/hour
# shortcut: per-process cache, fine for one Render instance; move to the database if it scales out
_standings: dict[tuple[str, int], tuple[float, list[dict]]] = {}


@router.get("/matches", response_model=list[MatchOut])
def list_matches(
    status: str | None = Query(None, description="not_started | running | finished"),
    videogame: str | None = Query(None, description="e.g. league-of-legends, cs-go, dota-2"),
    since: datetime | None = Query(None, description="scheduled at or after (ISO 8601)"),
    until: datetime | None = Query(None, description="scheduled before (ISO 8601)"),
    team: str | None = Query(None, description="team name, any game, case-insensitive"),
    league: str | None = Query(None, description="exact league name, e.g. LEC"),
    team_id: int | None = Query(None, description="one team, by id"),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[Match]:
    query = select(Match).options(selectinload(Match.team1), selectinload(Match.team2))
    if status:
        query = query.where(Match.status == status)
    if videogame:
        query = query.where(Match.videogame == videogame)
    if team:
        same = func.lower(Team.name) == team.strip().lower()
        query = query.where(or_(Match.team1.has(same), Match.team2.has(same)))
    if league:
        query = query.where(Match.league_name == league)
    if team_id is not None:
        query = query.where(or_(Match.team1_id == team_id, Match.team2_id == team_id))
    if since:
        query = query.where(Match.scheduled_at >= since)
    if until:
        query = query.where(Match.scheduled_at < until)
    order = Match.scheduled_at.desc() if status == "finished" else Match.scheduled_at.asc()
    return list(db.scalars(query.order_by(order).limit(limit)))


@router.get("/matches/{match_id}", response_model=MatchDetailOut)
def get_match(match_id: int, db: Session = Depends(get_db)) -> Match:
    """One match with its games, both rosters and the main stream."""
    match = db.get(
        Match,
        match_id,
        options=[
            selectinload(Match.team1).selectinload(Team.players),
            selectinload(Match.team2).selectinload(Team.players),
            selectinload(Match.games),
        ],
    )
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")
    return match


def _tournament_data(match_id: int, kind: str, db: Session) -> list[dict]:
    """A PandaScore tournament endpoint ("standings" or "brackets"), cached 10 minutes."""
    match = db.get(Match, match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")
    if match.source != "pandascore" or match.tournament_id is None:
        return []
    key = (kind, match.tournament_id)
    cached = _standings.get(key)
    if cached and time.monotonic() - cached[0] < STANDINGS_TTL:
        return cached[1]
    settings = get_settings()
    try:
        with PandaScoreClient(settings.pandascore_token, settings.pandascore_base_url) as client:
            rows = getattr(client, kind)(match.tournament_id)
    except Exception:
        log.exception("%s fetch failed for tournament %s", kind, match.tournament_id)
        return cached[1] if cached else []  # stale beats empty
    _standings[key] = (time.monotonic(), rows)
    return rows


@router.get("/matches/{match_id}/standings", response_model=list[StandingOut])
def get_standings(match_id: int, db: Session = Depends(get_db)) -> list[dict]:
    """Standings of the match's tournament, fetched from PandaScore and cached for 10 minutes."""
    return _tournament_data(match_id, "standings", db)


@router.get("/matches/{match_id}/bracket", response_model=list[BracketMatch])
def get_bracket(match_id: int, db: Session = Depends(get_db)) -> list[dict]:
    """Playoff tree of the match's tournament; empty when its matches are not linked (groups)."""
    return layout_bracket(_tournament_data(match_id, "brackets", db))


def layout_bracket(raw: list[dict]) -> list[dict]:
    """Place each match in the upper or lower bracket and in a round column, from previous_matches.

    A match fed by a loser, or by a lower-bracket winner, is in the lower bracket, unless an
    upper-bracket winner also feeds it (the grand final). Its round is one more than its latest
    same-bracket feeder.
    """
    if not any(m.get("previous_matches") for m in raw):
        return []
    by_id = {m["id"]: m for m in raw}
    side: dict[int, str] = {}
    rnd: dict[int, int] = {}

    def place(mid: int, seen: frozenset = frozenset()) -> None:
        if mid in side or mid in seen:
            return
        prev = [p for p in by_id[mid].get("previous_matches") or [] if p["match_id"] in by_id]
        for p in prev:
            place(p["match_id"], seen | {mid})
        win = [side.get(p["match_id"]) for p in prev if p["type"] == "winner"]
        lower = any(p["type"] == "loser" for p in prev) or "lower" in win
        side[mid] = "lower" if lower and "upper" not in win else "upper"
        same = [
            rnd.get(p["match_id"], 0)
            for p in prev
            if side.get(p["match_id"]) == side[mid] and p["type"] == "winner"
        ]
        rnd[mid] = 1 + max(same, default=0)

    for mid in by_id:
        place(mid)
    out = []
    for m in sorted(raw, key=lambda m: m["id"]):
        scores = {r["team_id"]: r["score"] for r in m.get("results") or []}
        teams = [o["opponent"] for o in m.get("opponents") or [] if o.get("opponent")]
        out.append(
            {
                "id": m["id"],
                "name": m.get("name") or "",
                "status": m.get("status") or "not_started",
                "scheduled_at": m.get("scheduled_at"),
                "winner_id": m.get("winner_id"),
                "bracket": side[m["id"]],
                "round": rnd[m["id"]],
                "teams": [{**t, "score": scores.get(t["id"])} for t in teams],
            }
        )
    return out


@router.get("/teams", response_model=list[TeamSuggestion])
def search_teams(
    q: str = Query(..., min_length=2, description="part of a team name"),
    db: Session = Depends(get_db),
) -> list[TeamSuggestion]:
    """Distinct team names with a logo, for the "My team" search box."""
    query = (
        select(Team.name, func.max(Team.image_url))  # one logo per name, any non-empty one
        .where(Team.name.ilike(f"%{q.strip()}%"))
        .group_by(Team.name)
        .order_by(Team.name)
        .limit(20)
    )
    return [TeamSuggestion(name=name, image_url=url) for name, url in db.execute(query)]


@router.get("/teams/{team_id}", response_model=TeamDetailOut)
def get_team(team_id: int, db: Session = Depends(get_db)) -> Team:
    team = db.get(Team, team_id, options=[selectinload(Team.players)])
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@router.get("/players/{player_id}", response_model=PlayerDetailOut)
def get_player(player_id: int, db: Session = Depends(get_db)) -> Player:
    player = db.get(Player, player_id, options=[selectinload(Player.team)])
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")
    return player


@router.get("/leagues", response_model=list[LeagueOut])
def list_leagues(
    videogame: str = Query(..., description="game slug, e.g. valorant"),
    db: Session = Depends(get_db),
) -> list[LeagueOut]:
    """Leagues of one game that have matches in the database, busiest first."""
    rows = db.execute(
        select(Match.league_name, func.max(Match.league_image_url), func.count(Match.id))
        .where(Match.videogame == videogame, Match.league_name.is_not(None))
        .group_by(Match.league_name)
        .order_by(func.count(Match.id).desc(), Match.league_name)
    ).all()
    return [LeagueOut(name=n, image_url=u, matches=c) for n, u, c in rows]


@router.get("/videogames", response_model=list[VideogameOut])
def list_videogames(db: Session = Depends(get_db)) -> list[VideogameOut]:
    rows = db.execute(
        select(Match.videogame, func.count(Match.id))
        .group_by(Match.videogame)
        .order_by(Match.videogame)
    ).all()
    return [VideogameOut(slug=slug, matches=count) for slug, count in rows]
