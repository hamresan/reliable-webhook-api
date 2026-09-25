from httpx import ASGITransport, AsyncClient
from pytest import MonkeyPatch

from reliable_webhook_api.config import get_settings
from reliable_webhook_api.presentation.api.app import create_app
from tests.api.support import sign


async def test_development_swagger_signs_exact_request_body(
    monkeypatch: MonkeyPatch,
) -> None:
    secret = "swagger-development-secret"
    monkeypatch.setenv("APP_ENVIRONMENT", "development")
    monkeypatch.setenv("APP_WEBHOOK_SECRET", secret)
    get_settings.cache_clear()

    try:
        app = create_app()
        payload = b'{"event_id":"exact-bytes"}'

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/docs/webhook-signature",
                content=payload,
                headers={"content-type": "text/plain"},
            )

        assert response.status_code == 200
        assert response.json() == {"signature": sign(secret, payload)}
    finally:
        get_settings.cache_clear()


async def test_development_swagger_injects_webhook_signing_interceptor(
    monkeypatch: MonkeyPatch,
) -> None:
    secret = "must-not-appear-in-docs"
    monkeypatch.setenv("APP_ENVIRONMENT", "development")
    monkeypatch.setenv("APP_WEBHOOK_SECRET", secret)
    get_settings.cache_clear()

    try:
        app = create_app()

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/docs")

        assert response.status_code == 200
        assert "/docs/webhook-signature" in response.text
        assert "X-Webhook-Signature" in response.text
        assert secret not in response.text
    finally:
        get_settings.cache_clear()


async def test_swagger_signing_endpoint_is_not_available_in_production(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_ENVIRONMENT", "production")
    monkeypatch.setenv("APP_WEBHOOK_SECRET", "production-secret")
    monkeypatch.setenv(
        "APP_DATABASE_URL",
        "postgresql+asyncpg://webhook:webhook@localhost:5432/webhook",
    )
    get_settings.cache_clear()

    try:
        app = create_app()

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/docs/webhook-signature",
                content=b"{}",
            )

        assert response.status_code == 404
    finally:
        get_settings.cache_clear()
