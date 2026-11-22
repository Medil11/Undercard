"""Pull matches from PandaScore and upsert them into the database.

Usage:
    python -m ingestion.sync
    python -m ingestion.sync --loop --interval 60
"""

import argparse
import logging
import time
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, delete, or_, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import SessionLocal
from app.models import Game, Match, Player, SyncStatus, Team
from ingestion.pandascore_client import MAX_PAGE_SIZE, STATUSES, PandaScoreClient
from ingestion.startgg import StartggClient, sync_startgg

log = logging.getLogger("ingestion")

# 100 upcoming matches only cover about a day and a half: take two pages so "Tomorrow" is complete.
PAGES = {"running": 1, "upcoming": 2, "past": 1}
STALE_AFTER = timedelta(minutes=30)  # a not_started match this late is re-checked by id
RETENTION = timedelta(days=30)  # matches older than this are deleted


def parse_dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


def parse_match(payload: dict) -> tuple[dict, list[dict]]:
    """Convert a PandaScore match payload into (match_fields, team_fields)."""
    opponents = [o["opponent"] for o in payload.get("opponents", []) if o.get("opponent")]
    scores = {r["team_id"]: r.get("score") for r in payload.get("results", [])}
    team1 = opponents[0] if len(opponents) > 0 else None
    team2 = opponents[1] if len(opponents) > 1 else None

    league = payload.get("league") or {}
    tournament = payload.get("tournament") or {}
    serie = payload.get("serie") or {}
    match = {
        "id": payload["id"],
        "videogame": (payload.get("videogame") or {}).get("slug", "unknown"),
        "name": payload.get("name") or "TBD",
        "status": payload["status"],
        "league_name": league.get("name"),
        "tournament_name": tournament.get("name"),
        "league_image_url": league.get("image_url"),
        "tournament_id": tournament.get("id"),
        "prizepool": tournament.get("prizepool"),
        "region": tournament.get("region"),
        "country": tournament.get("country"),
        "serie_name": serie.get("full_name"),
        "season": str(serie["season"]) if serie.get("season") is not None else None,
        "year": serie.get("year"),
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
        .where(Team.source == "pandascore")
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


def delete_match(session: Session, match: Match) -> None:
    session.execute(delete(Game).where(Game.match_id == match.id))
    session.delete(match)


def refresh_stale(session: Session, client: PandaScoreClient, seen: set[int], now: datetime) -> int:
    """Re-check matches that left the provider's lists without a final status.

    A postponed, cancelled or deleted match drops out of /running and /upcoming, so without this
    it would stay "upcoming" forever with a date in the past. One request per call at most.
    """
    stale = session.scalars(
        select(Match)
        .where(
            Match.source == "pandascore",
            Match.id.not_in(seen),
            or_(
                Match.status == "running",
                and_(Match.status == "not_started", Match.scheduled_at < now - STALE_AFTER),
            ),
        )
        .order_by(Match.scheduled_at)
        .limit(MAX_PAGE_SIZE)
    ).all()
    if not stale:
        return 0
    fresh = {p["id"]: p for p in client.matches_by_ids([m.id for m in stale])}
    removed = 0
    for match in stale:
        payload = fresh.get(match.id)
        if payload is None or not is_team_match(payload):
            delete_match(session, match)  # gone from the provider: do not keep a ghost
            removed += 1
        else:
            upsert_match(session, payload)
    session.commit()
    log.info("re-checked %d stale matches, removed %d", len(stale), removed)
    return len(stale)


def purge_old(session: Session, now: datetime, retention: timedelta = RETENTION) -> int:
    """Delete matches (and their games) scheduled before the retention window."""
    old = select(Match.id).where(Match.scheduled_at < now - retention)
    session.execute(delete(Game).where(Game.match_id.in_(old)))
    purged = session.execute(delete(Match).where(Match.scheduled_at < now - retention)).rowcount
    session.commit()
    if purged:
        log.info("purged %d matches older than %d days", purged, retention.days)
    return purged


def record_sync(
    session: Session, now: datetime, count: int | None = None, error: str | None = None
) -> None:
    status = session.get(SyncStatus, 1) or SyncStatus(id=1)
    if error is None:
        status.last_success_at, status.last_count = now, count
    else:
        status.last_error_at, status.last_error = now, error[:500]
    session.add(status)
    session.commit()


def sync_once(
    session: Session,
    client: PandaScoreClient,
    statuses: tuple[str, ...] = STATUSES,
    per_page: int = MAX_PAGE_SIZE,
    now: datetime | None = None,
    startgg: StartggClient | None = None,
) -> int:
    now = now or datetime.now(UTC)
    count = skipped = 0
    seen: set[int] = set()
    for status in statuses:
        for page in range(1, PAGES.get(status, 1) + 1):
            for payload in client.matches(status, per_page=per_page, page=page):
                if not is_team_match(payload):
                    skipped += 1
                    continue
                upsert_match(session, payload)
                seen.add(payload["id"])
                count += 1
    session.commit()
    log.info("synced %d matches, skipped %d player matches", count, skipped)
    refresh_stale(session, client, seen, now)
    refresh_rosters(session, client, now=now)
    if startgg is not None:
        try:  # a start.gg outage must not stop the PandaScore data
            count += sync_startgg(session, startgg, now=now)
        except Exception:
            session.rollback()
            log.exception("start.gg sync failed")
    purge_old(session, now)
    record_sync(session, now, count=count)
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync esports matches from PandaScore")
    parser.add_argument("--loop", action="store_true", help="run forever")
    parser.add_argument("--interval", type=int, default=60, help="seconds between runs")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = get_settings()

    startgg = StartggClient(settings.startgg_token) if settings.startgg_token else None
    with PandaScoreClient(settings.pandascore_token, settings.pandascore_base_url) as client:
        while True:
            try:
                with SessionLocal() as session:
                    sync_once(session, client, startgg=startgg)
            except Exception as exc:
                log.exception("sync failed")
                with SessionLocal() as session:
                    record_sync(session, datetime.now(UTC), error=repr(exc))
                if not args.loop:
                    raise
            if not args.loop:
                break
            time.sleep(args.interval)


if __name__ == "__main__":
    main()
