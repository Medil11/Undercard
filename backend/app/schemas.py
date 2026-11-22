from datetime import UTC, date, datetime

from pydantic import BaseModel, ConfigDict, field_validator


class TeamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    acronym: str | None = None
    image_url: str | None = None


class MatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str = "pandascore"
    videogame: str
    name: str
    status: str
    league_name: str | None = None
    tournament_name: str | None = None
    league_image_url: str | None = None
    tier: str | None = None
    prizepool: str | None = None
    region: str | None = None
    country: str | None = None
    serie_name: str | None = None
    season: str | None = None
    year: int | None = None
    scheduled_at: datetime | None = None
    begin_at: datetime | None = None
    end_at: datetime | None = None
    number_of_games: int | None = None
    match_type: str | None = None
    team1: TeamOut | None = None
    team2: TeamOut | None = None
    team1_score: int | None = None
    team2_score: int | None = None
    winner_id: int | None = None

    @field_validator("scheduled_at", "begin_at", "end_at")
    @classmethod
    def assume_utc(cls, value: datetime | None) -> datetime | None:
        """Times are stored in UTC; SQLite drops the offset, so put it back for the browser."""
        return value.replace(tzinfo=UTC) if value and value.tzinfo is None else value


class PlayerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    first_name: str | None = None
    last_name: str | None = None
    role: str | None = None
    nationality: str | None = None
    image_url: str | None = None
    birthday: date | None = None


class TeamDetailOut(TeamOut):
    players: list[PlayerOut] = []


class PlayerDetailOut(PlayerOut):
    team: TeamOut | None = None


class GameOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    position: int
    status: str
    winner_id: int | None = None
    length: int | None = None


class MatchDetailOut(MatchOut):
    team1: TeamDetailOut | None = None
    team2: TeamDetailOut | None = None
    games: list[GameOut] = []
    stream_url: str | None = None


class StandingMatch(BaseModel):
    id: int
    name: str
    status: str
    winner_id: int | None = None


class StandingOut(BaseModel):
    rank: int
    team: TeamOut
    last_match: StandingMatch | None = None


class LeagueOut(BaseModel):
    name: str
    image_url: str | None = None
    matches: int


class TeamSuggestion(BaseModel):
    name: str
    image_url: str | None = None


class VideogameOut(BaseModel):
    slug: str
    matches: int
