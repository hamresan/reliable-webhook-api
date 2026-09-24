from datetime import UTC, datetime, timedelta
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
    SqlAlchemyEventQuery,
    SqlAlchemyEventRepository,
    SqlAlchemyUnitOfWork,
)

NOW = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)


def build_event(index: int, status: EventStatus, retry_at: datetime | None = None) -> WebhookEvent:
    return WebhookEvent(
        id=EventId(UUID(int=index + 1)),
        event_type=EventType("invoice.paid"),
        occurred_at=OccurredAt(NOW + timedelta(seconds=index)),
        data={"index": index},
        status=status,
        received_at=ReceivedAt(NOW + timedelta(seconds=index)),
        next_retry_at=retry_at,
    )


async def persist(
    session_factory: async_sessionmaker[AsyncSession],
    events: list[WebhookEvent],
) -> None:
    async with session_factory() as session:
        repository = SqlAlchemyEventRepository(session)
        async with SqlAlchemyUnitOfWork(session):
            for event in events:
                await repository.add(event)


async def test_query_filters_and_paginates_with_total(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    events = [
        build_event(0, EventStatus.FAILED),
        build_event(1, EventStatus.PROCESSED),
        build_event(2, EventStatus.FAILED),
    ]
    await persist(session_factory, events)

    async with session_factory() as session:
        page = await SqlAlchemyEventQuery(session).page(EventStatus.FAILED, offset=1, limit=1)

    assert page.total == 2
    assert [event.id for event in page.items] == [events[2].id]


async def test_due_retry_selection_excludes_future_and_other_states(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    due = build_event(0, EventStatus.RETRY_SCHEDULED, NOW - timedelta(seconds=1))
    future = build_event(1, EventStatus.RETRY_SCHEDULED, NOW + timedelta(seconds=1))
    failed = build_event(2, EventStatus.FAILED, NOW - timedelta(seconds=1))
    await persist(session_factory, [due, future, failed])

    async with session_factory() as session:
        events = await SqlAlchemyEventQuery(session).due_retries(NOW, limit=10)

    assert [event.id for event in events] == [due.id]
