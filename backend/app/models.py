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
    team1_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    team2_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    team1_score: Mapped[int | None]
    team2_score: Mapped[int | None]
    winner_id: Mapped[int | None]
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    team1: Mapped[Team | None] = relationship(foreign_keys=[team1_id])
    team2: Mapped[Team | None] = relationship(foreign_keys=[team2_id])
