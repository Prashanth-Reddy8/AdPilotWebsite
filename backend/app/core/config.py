"""Typed application configuration loaded exclusively from the environment."""

from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings with safe validation for security-sensitive values."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_name: str = "AdPilot API"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    secret_key: str = Field(min_length=32)
    token_encryption_key: str
    database_url: str
    access_token_expire_minutes: int = Field(default=60, ge=5, le=1440)
    meta_app_id: str = ""
    meta_app_secret: str = ""
    meta_api_version: str = "v23.0"
    sync_scheduler_enabled: bool = True
    sync_interval_minutes: int = Field(default=60, ge=15, le=1440)
    log_level: str = "INFO"
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:8080"]
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    """Return one immutable-by-convention settings object per process."""

    return Settings()  # type: ignore[call-arg]
