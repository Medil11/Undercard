from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./esport_live.db"
    pandascore_token: str = ""
    pandascore_base_url: str = "https://api.pandascore.co"
    # Optional: fighting games from start.gg. Empty disables that source.
    startgg_token: str = ""
    # Shared with the Supabase cron job that calls POST /internal/sync. Empty disables the route.
    sync_secret: str = ""

    @field_validator("database_url")
    @classmethod
    def use_psycopg_driver(cls, url: str) -> str:
        """Accept the plain postgres:// URLs Supabase and Render hand out."""
        for prefix in ("postgres://", "postgresql://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url[len(prefix) :]
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()
