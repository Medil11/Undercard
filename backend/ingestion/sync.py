"""Pull matches from PandaScore and upsert them into the database.

Usage:
    python -m ingestion.sync
    python -m ingestion.sync --loop --interval 60
"""

import argparse
import logging
import time
from datetime import datetime

from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import Base, SessionLocal, engine
from app.models import Match, Team
from ingestion.pandascore_client import STATUSES, PandaScoreClient

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
        "team1_id": team1["id"] if team1 else None,
        "team2_id": team2["id"] if team2 else None,
        "team1_score": scores.get(team1["id"]) if team1 else None,
        "team2_score": scores.get(team2["id"]) if team2 else None,
        "winner_id": payload.get("winner_id"),
    }
    teams = [
        {k: t.get(k) for k in ("id", "name", "acronym", "image_url")} for t in (team1, team2) if t
    ]
    return match, teams


def upsert_match(session: Session, payload: dict) -> None:
    match, teams = parse_match(payload)
    for team in teams:
        session.merge(Team(**team))
    session.flush()  # teams must exist before the match references them
    session.merge(Match(**match))


def sync_once(
    session: Session,
    client: PandaScoreClient,
    statuses: tuple[str, ...] = STATUSES,
    per_page: int = 50,
) -> int:
    count = 0
    for status in statuses:
        for payload in client.matches(status, per_page=per_page):
            upsert_match(session, payload)
            count += 1
    session.commit()
    log.info("synced %d matches", count)
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
