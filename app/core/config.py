from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "AI Sales and Lead Intelligence Backend"
    app_version: str = "0.1.0"
    api_prefix: str = "/api"
    app_env: str = "development"
    log_level: str = "INFO"

    database_url: str = Field(default="", alias="DATABASE_URL")
    allowed_origins: list[str] = Field(default_factory=lambda: ["*"])

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
