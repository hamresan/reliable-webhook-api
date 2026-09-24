from datetime import timedelta
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "Reliable Webhook API"
    environment: str = "development"
    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)
    webhook_secret: str = ""
    webhook_signature_header: str = "X-Webhook-Signature"
    database_url: str = "postgresql+asyncpg://webhook:webhook@localhost:5432/webhook"
    retry_max_attempts: int = Field(default=3, ge=1, le=100)
    retry_base_delay_seconds: int = Field(default=30, ge=1)
    retry_max_delay_seconds: int = Field(default=3600, ge=1)

    @property
    def retry_base_delay(self) -> timedelta:
        return timedelta(seconds=self.retry_base_delay_seconds)

    @property
    def retry_max_delay(self) -> timedelta:
        return timedelta(seconds=self.retry_max_delay_seconds)

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
