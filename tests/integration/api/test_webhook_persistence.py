from uuid import UUID

from httpx import ASGITransport, AsyncClient
from pytest import MonkeyPatch
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from reliable_webhook_api.config import get_settings
from reliable_webhook_api.infrastructure.persistence import SqlAlchemyEventRepository
from reliable_webhook_api.presentation.api.app import create_app
from reliable_webhook_api.presentation.api.dependencies.webhooks import (
    get_database_engine,
    get_session_factory,
)
from tests.api.support import sign

SECRET = "stage-three-api-secret"
EVENT_ID = UUID("00000000-0000-0000-0000-000000000301")


async def test_api_uses_real_repository_and_dependency_wiring(
    session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_WEBHOOK_SECRET", SECRET)
    get_settings.cache_clear()
    get_database_engine.cache_clear()
    get_session_factory.cache_clear()

    payload = (
        b'{"event_id":"00000000-0000-0000-0000-000000000301",'
        b'"event_type":"invoice.paid","occurred_at":"2026-09-24T12:00:00Z",'
        b'"data":{"invoice_id":"inv-real"}}'
    )
    headers = {
        "content-type": "application/json",
        "X-Webhook-Signature": sign(SECRET, payload),
    }
    app = create_app()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        first = await client.post("/webhooks/events", content=payload, headers=headers)
        second = await client.post("/webhooks/events", content=payload, headers=headers)

    assert first.status_code == 202
    assert second.status_code == 200
    assert second.json()["duplicate"] is True

    async with session_factory() as session:
        events = await SqlAlchemyEventRepository(session).list()

    assert len(events) == 1
    assert events[0].id.value == EVENT_ID
