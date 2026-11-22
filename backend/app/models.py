from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _now() -> datetime:
    return datetime.now(UTC)


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    acronym: Mapped[str | None] = mapped_column(String(50))
    image_url: Mapped[str | None] = mapped_column(String(500))
    # Rosters come from a separate, rate-limited endpoint, so they are refreshed on their own clock.
    roster_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    players: Mapped[list["Player"]] = relationship(order_by="Player.name")


class Player(Base):
    """Current roster member of a team (not necessarily in the lineup of a given match)."""

    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    first_name: Mapped[str | None] = mapped_column(String(200))
    last_name: Mapped[str | None] = mapped_column(String(200))
    role: Mapped[str | None] = mapped_column(String(50))
    nationality: Mapped[str | None] = mapped_column(String(10))
    image_url: Mapped[str | None] = mapped_column(String(500))


class Game(Base):
    """One map / game of a series."""

    __tablename__ = "games"

    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), index=True)
    position: Mapped[int]
    status: Mapped[str] = mapped_column(String(20))
    winner_id: Mapped[int | None]
    length: Mapped[int | None]  # seconds


class SyncStatus(Base):
    """Single row (id=1) describing the last ingestion cycles, read by /health/sync."""

    __tablename__ = "sync_status"

    id: Mapped[int] = mapped_column(primary_key=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_count: Mapped[int | None]
    last_error_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(String(500))


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    videogame: Mapped[str] = mapped_column(String(50), index=True)
    name: Mapped[str] = mapped_column(String(300))
    # PandaScore statuses: not_started | running | finished | canceled | postponed
    status: Mapped[str] = mapped_column(String(20), index=True)
    league_name: Mapped[str | None] = mapped_column(String(200))
    tournament_name: Mapped[str | None] = mapped_column(String(200))
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    begin_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    number_of_games: Mapped[int | None]
    # best_of: number_of_games is the series length; first_to: it is the wins needed (Overwatch).
    match_type: Mapped[str | None] = mapped_column(String(20))
    team1_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    team2_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    team1_score: Mapped[int | None]
    team2_score: Mapped[int | None]
    winner_id: Mapped[int | None]
    stream_url: Mapped[str | None] = mapped_column(String(500))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    team1: Mapped[Team | None] = relationship(foreign_keys=[team1_id])
    team2: Mapped[Team | None] = relationship(foreign_keys=[team2_id])
    games: Mapped[list[Game]] = relationship(order_by=Game.position)
