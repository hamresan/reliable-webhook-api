import asyncio
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from reliable_webhook_api.application.dto import EventInput, ReceiveWebhookEventInput
from reliable_webhook_api.application.use_cases import ReceiveWebhookEvent
from reliable_webhook_api.infrastructure.clock import SystemClock
from reliable_webhook_api.infrastructure.persistence import (
    SqlAlchemyEventRepository,
    SqlAlchemyUnitOfWork,
)
from reliable_webhook_api.infrastructure.security import HmacSha256SignatureVerifier
from tests.api.support import sign

SECRET = "stage-three-concurrency-secret"
EVENT_ID = UUID("00000000-0000-0000-0000-000000000201")
NOW = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)
RAW_PAYLOAD = b'{"event":"same-id"}'


async def receive_once(session_factory: async_sessionmaker[AsyncSession]):
    async with session_factory() as session:
        use_case = ReceiveWebhookEvent(
            repository=SqlAlchemyEventRepository(session),
            signature_verifier=HmacSha256SignatureVerifier(SECRET),
            clock=SystemClock(),
            unit_of_work=SqlAlchemyUnitOfWork(session),
        )
        return await use_case.execute(
            ReceiveWebhookEventInput(
                raw_payload=RAW_PAYLOAD,
                signature=sign(SECRET, RAW_PAYLOAD),
                event=EventInput(
                    event_id=EVENT_ID,
                    event_type="invoice.paid",
                    occurred_at=NOW,
                    data={"invoice_id": "inv-concurrent"},
                ),
            )
        )


async def test_concurrent_same_id_persists_once_and_returns_stable_duplicate(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    first, second = await asyncio.gather(
        receive_once(session_factory),
        receive_once(session_factory),
    )

    assert sorted([first.duplicate, second.duplicate]) == [False, True]
    async with session_factory() as session:
        events = await SqlAlchemyEventRepository(session).list()
    assert len(events) == 1
    assert events[0].id.value == EVENT_ID
