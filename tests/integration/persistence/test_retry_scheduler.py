from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from reliable_webhook_api.domain import (
    EventId,
    EventStatus,
    EventType,
    OccurredAt,
    ReceivedAt,
    WebhookEvent,
)
from reliable_webhook_api.infrastructure.persistence import (
    SqlAlchemyEventRepository,
    SqlAlchemyUnitOfWork,
)
from reliable_webhook_api.infrastructure.scheduling import SqlAlchemyRetryScheduler

NOW = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)


async def test_scheduler_persists_due_time_in_same_transaction(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    event = WebhookEvent(
        id=EventId(UUID("00000000-0000-0000-0000-000000000506")),
        event_type=EventType("invoice.paid"),
        occurred_at=OccurredAt(NOW),
        data={},
        status=EventStatus.RETRY_SCHEDULED,
        received_at=ReceivedAt(NOW),
    )
    async with session_factory() as session:
        repository = SqlAlchemyEventRepository(session)
        async with SqlAlchemyUnitOfWork(session):
            await repository.add(event)
            await SqlAlchemyRetryScheduler(session).schedule(event.id, NOW)

    async with session_factory() as session:
        persisted = await SqlAlchemyEventRepository(session).get(event.id)

    assert persisted is not None
    assert persisted.next_retry_at == NOW
