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
_standings: dict[int, tuple[float, list[dict]]] = {}


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


@router.get("/matches/{match_id}/standings", response_model=list[StandingOut])
def get_standings(match_id: int, db: Session = Depends(get_db)) -> list[dict]:
    """Standings of the match's tournament, fetched from PandaScore and cached for 10 minutes."""
    match = db.get(Match, match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")
    if match.source != "pandascore" or match.tournament_id is None:
        return []
    cached = _standings.get(match.tournament_id)
    if cached and time.monotonic() - cached[0] < STANDINGS_TTL:
        return cached[1]
    settings = get_settings()
    try:
        with PandaScoreClient(settings.pandascore_token, settings.pandascore_base_url) as client:
            rows = client.standings(match.tournament_id)
    except Exception:
        log.exception("standings fetch failed for tournament %s", match.tournament_id)
        return cached[1] if cached else []  # stale beats empty
    _standings[match.tournament_id] = (time.monotonic(), rows)
    return rows


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
