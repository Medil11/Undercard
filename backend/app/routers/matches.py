from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import Match, Team
from app.schemas import MatchDetailOut, MatchOut, VideogameOut

router = APIRouter(tags=["matches"])


@router.get("/matches", response_model=list[MatchOut])
def list_matches(
    status: str | None = Query(None, description="not_started | running | finished"),
    videogame: str | None = Query(None, description="e.g. league-of-legends, cs-go, dota-2"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[Match]:
    query = select(Match).options(selectinload(Match.team1), selectinload(Match.team2))
    if status:
        query = query.where(Match.status == status)
    if videogame:
        query = query.where(Match.videogame == videogame)
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


@router.get("/videogames", response_model=list[VideogameOut])
def list_videogames(db: Session = Depends(get_db)) -> list[VideogameOut]:
    rows = db.execute(
        select(Match.videogame, func.count(Match.id))
        .group_by(Match.videogame)
        .order_by(Match.videogame)
    ).all()
    return [VideogameOut(slug=slug, matches=count) for slug, count in rows]
