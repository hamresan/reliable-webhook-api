from pathlib import Path

from reliable_webhook_api.config.settings import Settings


def test_settings_use_safe_defaults_without_required_secrets() -> None:
    settings = Settings(_env_file=None)

    assert settings.app_name == "Reliable Webhook API"
    assert settings.environment == "development"
    assert settings.host == "0.0.0.0"
    assert settings.port == 8000


def test_test_configuration_does_not_read_real_env_file(
    tmp_path: Path,
    monkeypatch,
) -> None:
    (tmp_path / ".env").write_text("APP_ENVIRONMENT=production\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    settings = Settings(_env_file=None)

    assert settings.environment == "development"
