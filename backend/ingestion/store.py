"""Write a match with its teams and games, only if changed since this process last wrote it."""

from sqlalchemy.orm import Session

from app.models import Game, Match, Team

# merge() reads every row back before comparing, and on Supabase each read counts as egress.
# shortcut: per-process memory that assumes a single writer; restart the service after editing
# or restoring the database by other means.
written: dict[int, int] = {}  # match id -> hash of what was last written


def save_match(session: Session, match: dict, teams: list[dict], games: list[dict]) -> None:
    fingerprint = hash(repr((match, teams, games)))
    if written.get(match["id"]) == fingerprint:
        return
    for team in teams:
        session.merge(Team(**team))
    session.flush()  # teams must exist before the match references them
    session.merge(Match(**match))
    session.flush()  # the match must exist before its games reference it
    for game in games:
        session.merge(Game(**game))
    written[match["id"]] = fingerprint
