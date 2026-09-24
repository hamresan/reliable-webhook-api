from collections.abc import Coroutine
from typing import Any

from httpx import ASGITransport, AsyncClient

from reliable_webhook_api.infrastructure.health import DatabaseReadinessChecker
from reliable_webhook_api.presentation.api.app import create_app
from reliable_webhook_api.presentation.api.dependencies.health import get_readiness_checker


class FakeReadinessChecker(DatabaseReadinessChecker):
    def __init__(self, ready: bool) -> None:
        self._ready = ready

    async def is_ready(self) -> bool:
        return self._ready


async def test_health_returns_ok_and_correlation_id() -> None:
    app = create_app()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/health", headers={"X-Request-ID": "request-123"})

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Request-ID"] == "request-123"


async def test_readiness_returns_ready_when_database_is_available() -> None:
    app = create_app()
    app.dependency_overrides[get_readiness_checker] = lambda: FakeReadinessChecker(True)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


async def test_readiness_maps_database_failure_to_503() -> None:
    app = create_app()
    app.dependency_overrides[get_readiness_checker] = lambda: FakeReadinessChecker(False)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": "Service is not ready."}
