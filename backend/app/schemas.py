from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TeamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    acronym: str | None = None
    image_url: str | None = None


class MatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    videogame: str
    name: str
    status: str
    league_name: str | None = None
    tournament_name: str | None = None
    scheduled_at: datetime | None = None
    begin_at: datetime | None = None
    end_at: datetime | None = None
    number_of_games: int | None = None
    team1: TeamOut | None = None
    team2: TeamOut | None = None
    team1_score: int | None = None
    team2_score: int | None = None
    winner_id: int | None = None


class VideogameOut(BaseModel):
    slug: str
    matches: int
