import asyncio
from datetime import UTC, datetime
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from reliable_webhook_api.application.errors import DuplicateEventError
from reliable_webhook_api.domain import (
    AttemptNumber,
    EventId,
    EventStatus,
    EventType,
    FailureCode,
    FailureMessage,
    FailureReason,
    OccurredAt,
    ProcessingAttempt,
    ProcessingPeriod,
    ProcessingTimestamp,
    ReceivedAt,
    WebhookEvent,
)
from reliable_webhook_api.infrastructure.persistence import (
    SqlAlchemyEventRepository,
    SqlAlchemyUnitOfWork,
)

EVENT_ID = UUID("00000000-0000-0000-0000-000000000101")
NOW = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)


def build_event(event_id: UUID = EVENT_ID) -> WebhookEvent:
    return WebhookEvent(
        id=EventId(event_id),
        event_type=EventType("invoice.paid"),
        occurred_at=OccurredAt(NOW),
        data={
            "nested": {"amount": 10.25, "paid": True},
            "items": [1, "two", None],
            "unicode": "سلام",
        },
        status=EventStatus.RECEIVED,
        received_at=ReceivedAt(NOW),
    )


async def test_save_retrieve_and_json_round_trip(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    event = build_event()
    async with session_factory() as session:
        repository = SqlAlchemyEventRepository(session)
        async with SqlAlchemyUnitOfWork(session):
            await repository.add(event)

    async with session_factory() as session:
        persisted = await SqlAlchemyEventRepository(session).get(event.id)

    assert persisted == event
    assert persisted is not None
    assert persisted.data == event.data


async def test_list_and_filter_events(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    received = build_event()
    processed = build_event(UUID("00000000-0000-0000-0000-000000000102"))
    processed.status = EventStatus.PROCESSED

    async with session_factory() as session:
        repository = SqlAlchemyEventRepository(session)
        async with SqlAlchemyUnitOfWork(session):
            await repository.add(received)
            await repository.add(processed)

    async with session_factory() as session:
        repository = SqlAlchemyEventRepository(session)
        all_events = await repository.list()
        processed_events = await repository.list(EventStatus.PROCESSED)

    assert {event.id for event in all_events} == {received.id, processed.id}
    assert [event.id for event in processed_events] == [processed.id]


async def test_update_persists_status_failure_and_attempt(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    event = build_event()
    async with session_factory() as session:
        repository = SqlAlchemyEventRepository(session)
        async with SqlAlchemyUnitOfWork(session):
            await repository.add(event)

    failure = FailureReason(FailureCode("handler_error"), FailureMessage("safe summary"))
    event.status = EventStatus.FAILED
    event.failure_reason = failure
    event.attempts.append(
        ProcessingAttempt(
            number=AttemptNumber(1),
            period=ProcessingPeriod(
                started_at=ProcessingTimestamp(NOW),
                finished_at=ProcessingTimestamp(NOW),
            ),
            failure_reason=failure,
        )
    )

    async with session_factory() as session:
        repository = SqlAlchemyEventRepository(session)
        async with SqlAlchemyUnitOfWork(session):
            await repository.save(event)

    async with session_factory() as session:
        persisted = await SqlAlchemyEventRepository(session).get(event.id)

    assert persisted == event


async def test_unique_event_id_is_translated_to_application_error(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    event = build_event()
    async with session_factory() as session:
        repository = SqlAlchemyEventRepository(session)
        async with SqlAlchemyUnitOfWork(session):
            await repository.add(event)

    async with session_factory() as session:
        repository = SqlAlchemyEventRepository(session)
        with pytest.raises(DuplicateEventError):
            await repository.add(build_event())

        persisted = await repository.get(event.id)

    assert persisted == event


async def test_processing_claim_is_atomic_across_workers(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    event = build_event()
    async with session_factory() as session, SqlAlchemyUnitOfWork(session):
        await SqlAlchemyEventRepository(session).add(event)

    async def claim() -> WebhookEvent | None:
        async with session_factory() as session, SqlAlchemyUnitOfWork(session):
            return await SqlAlchemyEventRepository(session).claim_for_processing(event.id)

    first, second = await asyncio.gather(claim(), claim())

    claimed = [result for result in (first, second) if result is not None]
    assert len(claimed) == 1
    assert claimed[0].status is EventStatus.PROCESSING
