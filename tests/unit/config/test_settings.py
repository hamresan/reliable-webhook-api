from pathlib import Path

import pytest
from pydantic import ValidationError
from pytest import MonkeyPatch

from reliable_webhook_api.config.settings import Settings


def test_settings_use_safe_defaults_without_required_secrets(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.delenv("APP_ENVIRONMENT", raising=False)

    settings = Settings(_env_file=None)  # pyright: ignore[reportCallIssue]

    assert settings.app_name == "Reliable Webhook API"
    assert settings.environment == "development"
    assert settings.host == "0.0.0.0"
    assert settings.port == 8000
    assert settings.webhook_secret == ""
    assert settings.webhook_signature_header == "X-Webhook-Signature"
    assert settings.logging_level == "INFO"
    assert settings.max_payload_bytes == 1_048_576


def test_test_configuration_does_not_read_real_env_file(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    (tmp_path / ".env").write_text("APP_ENVIRONMENT=production\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("APP_ENVIRONMENT", raising=False)

    settings = Settings(_env_file=None)  # pyright: ignore[reportCallIssue]

    assert settings.environment == "development"


def test_production_requires_webhook_secret() -> None:
    with pytest.raises(ValidationError):
        Settings(
            environment="production",
            webhook_secret="",
            database_url="postgresql+asyncpg://db",
            _env_file=None,  # pyright: ignore[reportCallIssue]
        )


def test_retry_max_delay_cannot_be_lower_than_base_delay() -> None:
    with pytest.raises(ValidationError):
        Settings(
            retry_base_delay_seconds=60,
            retry_max_delay_seconds=30,
            _env_file=None,  # pyright: ignore[reportCallIssue]
        )
