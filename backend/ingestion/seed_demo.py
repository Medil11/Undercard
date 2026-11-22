"""Fill the local database with fictional demo matches (no external API, no token needed).

Usage (from the backend folder):
    python -m ingestion.seed_demo
"""

# ruff: noqa: E501  (the demo table below is easier to read on one line per match)

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.db import SessionLocal, engine
from ingestion.sync import upsert_match

ID_OFFSET = 9_000_000  # keeps demo ids away from real provider ids

# (videogame, league, tournament, status, minutes from now, best of, team 1, acr, team 2, acr, score 1, score 2)
DEMO = [
    (
        "league-of-legends",
        "Ligue Démo",
        "Playoffs",
        "running",
        -34,
        5,
        "Nova Esports",
        "NOV",
        "Iron Wolves",
        "IRW",
        1,
        1,
    ),
    (
        "league-of-legends",
        "Ligue Démo",
        "Playoffs",
        "not_started",
        95,
        3,
        "Crimson Tide",
        "CRT",
        "Lunar Fox",
        "LNF",
        None,
        None,
    ),
    (
        "league-of-legends",
        "Ligue Démo",
        "Playoffs",
        "finished",
        -310,
        3,
        "Sky Forge",
        "SKF",
        "Pale Owls",
        "PLO",
        2,
        0,
    ),
    (
        "cs-go",
        "Open Series",
        "Phase de groupes",
        "running",
        -52,
        3,
        "Vortex",
        "VTX",
        "Static Void",
        "STV",
        1,
        0,
    ),
    (
        "cs-go",
        "Open Series",
        "Phase de groupes",
        "finished",
        -200,
        3,
        "Red Mirage",
        "RDM",
        "Echo Unit",
        "ECU",
        2,
        1,
    ),
    (
        "cs-go",
        "Open Series",
        "Phase de groupes",
        "not_started",
        1560,
        3,
        "Black Anchor",
        "BLA",
        "Zen Pack",
        "ZNP",
        None,
        None,
    ),
    (
        "dota-2",
        "Coupe Démo",
        "Quarts de finale",
        "running",
        -70,
        5,
        "Titan Root",
        "TTR",
        "Glass Cannon",
        "GLC",
        0,
        1,
    ),
    (
        "dota-2",
        "Coupe Démo",
        "Quarts de finale",
        "not_started",
        240,
        3,
        "Night Relay",
        "NRL",
        "Gold Harbor",
        "GDH",
        None,
        None,
    ),
    (
        "valorant",
        "Masters Démo",
        "Ronde suisse",
        "finished",
        -120,
        3,
        "Ember Squad",
        "EMB",
        "Frost Cell",
        "FRC",
        2,
        1,
    ),
    (
        "valorant",
        "Masters Démo",
        "Ronde suisse",
        "not_started",
        1440,
        3,
        "Pulse Drift",
        "PLD",
        "Neon Pact",
        "NNP",
        None,
        None,
    ),
    (
        "rl",
        "Série Démo",
        "Finale",
        "not_started",
        150,
        7,
        "Apex Orbit",
        "APX",
        "Rift Garage",
        "RFG",
        None,
        None,
    ),
]


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def build_payload(index: int, row: tuple, now: datetime) -> dict:
    vg, league, tournament, status, offset, bo, n1, a1, n2, a2, s1, s2 = row
    t1, t2 = ID_OFFSET + index * 2 + 1, ID_OFFSET + index * 2 + 2
    start = now + timedelta(minutes=offset)
    finished = status == "finished"
    return {
        "id": ID_OFFSET + index + 1,
        "name": f"{n1} vs {n2}",
        "status": status,
        "scheduled_at": _iso(start),
        "begin_at": _iso(start) if status != "not_started" else None,
        "end_at": _iso(start + timedelta(minutes=90)) if finished else None,
        "number_of_games": bo,
        "winner_id": (t1 if s1 > s2 else t2) if finished else None,
        "videogame": {"slug": vg},
        "league": {"name": league},
        "tournament": {"name": tournament},
        "opponents": [
            {"opponent": {"id": t1, "name": n1, "acronym": a1, "image_url": None}},
            {"opponent": {"id": t2, "name": n2, "acronym": a2, "image_url": None}},
        ],
        "results": []
        if s1 is None
        else [{"team_id": t1, "score": s1}, {"team_id": t2, "score": s2}],
    }


def seed(session: Session) -> int:
    now = datetime.now(UTC)
    for index, row in enumerate(DEMO):
        upsert_match(session, build_payload(index, row, now))
    session.commit()
    return len(DEMO)


def main() -> None:
    with SessionLocal() as session:
        count = seed(session)
    print(f"{count} demo matches written to {engine.url}")


if __name__ == "__main__":
    main()
