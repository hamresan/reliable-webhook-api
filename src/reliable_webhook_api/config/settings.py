from datetime import timedelta
from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "Reliable Webhook API"
    environment: Literal["development", "test", "production"] = "development"
    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)
    webhook_secret: str = ""
    webhook_signature_header: str = "X-Webhook-Signature"
    database_url: str = "postgresql+asyncpg://webhook:webhook@localhost:5432/webhook"
    retry_max_attempts: int = Field(default=3, ge=1, le=100)
    retry_base_delay_seconds: int = Field(default=30, ge=1)
    retry_max_delay_seconds: int = Field(default=3600, ge=1)
    logging_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    max_payload_bytes: int = Field(default=1_048_576, ge=1, le=10_485_760)

    @model_validator(mode="after")
    def validate_runtime_configuration(self) -> "Settings":
        if self.retry_max_delay_seconds < self.retry_base_delay_seconds:
            raise ValueError("retry_max_delay_seconds must be >= retry_base_delay_seconds")
        if self.environment == "production":
            if not self.webhook_secret.strip():
                raise ValueError("webhook_secret is required in production")
            if not self.database_url.strip():
                raise ValueError("database_url is required in production")
        return self

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
