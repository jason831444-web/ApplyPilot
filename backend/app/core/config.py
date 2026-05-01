from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ApplyPilot API"
    app_env: str = "development"
    database_url: str = "postgresql+psycopg://applypilot:applypilot@localhost:5432/applypilot"
    secret_key: str = "change-me-in-development"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    backend_cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"],
        validation_alias=AliasChoices("BACKEND_CORS_ORIGINS", "CORS_ORIGINS"),
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
