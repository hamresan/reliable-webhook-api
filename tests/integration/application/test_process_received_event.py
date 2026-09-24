from datetime import UTC, datetime
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from reliable_webhook_api.application.errors import InvalidTransitionError
from reliable_webhook_api.application.ports import EventProcessor
from reliable_webhook_api.application.processing import ProcessingFailureMapper
from reliable_webhook_api.application.use_cases import ProcessReceivedEvent
from reliable_webhook_api.domain import (
    EventId,
    EventStatus,
    EventTransitionPolicy,
    EventType,
    OccurredAt,
    ReceivedAt,
    WebhookEvent,
)
from reliable_webhook_api.infrastructure.clock import SystemClock
from reliable_webhook_api.infrastructure.persistence import (
    SqlAlchemyEventRepository,
    SqlAlchemyUnitOfWork,
)

EVENT_ID = EventId(UUID("00000000-0000-0000-0000-000000000404"))
NOW = datetime(2026, 9, 24, 14, 0, tzinfo=UTC)


class RecordingProcessor(EventProcessor):
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.calls = 0

    async def process(self, event: WebhookEvent) -> None:
        self.calls += 1
        if self.error is not None:
            raise self.error


def build_event() -> WebhookEvent:
    return WebhookEvent(
        id=EVENT_ID,
        event_type=EventType("invoice.paid"),
        occurred_at=OccurredAt(NOW),
        data={"invoice_id": "inv-404"},
        status=EventStatus.RECEIVED,
        received_at=ReceivedAt(NOW),
    )


async def persist_received_event(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        repository = SqlAlchemyEventRepository(session)
        async with SqlAlchemyUnitOfWork(session):
            await repository.add(build_event())


async def load_event(
    session_factory: async_sessionmaker[AsyncSession],
) -> WebhookEvent:
    async with session_factory() as session:
        event = await SqlAlchemyEventRepository(session).get(EVENT_ID)
    assert event is not None
    return event


async def process(
    session_factory: async_sessionmaker[AsyncSession],
    processor: RecordingProcessor,
) -> EventStatus:
    async with session_factory() as session:
        use_case = ProcessReceivedEvent(
            repository=SqlAlchemyEventRepository(session),
            processor=processor,
            clock=SystemClock(),
            unit_of_work=SqlAlchemyUnitOfWork(session),
            transition_policy=EventTransitionPolicy(),
            failure_mapper=ProcessingFailureMapper(),
        )
        return (await use_case.execute(EVENT_ID)).status


async def test_processing_success_is_persisted_and_not_processed_twice(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await persist_received_event(session_factory)
    processor = RecordingProcessor()

    status = await process(session_factory, processor)

    persisted = await load_event(session_factory)
    assert status is EventStatus.PROCESSED
    assert persisted.status is EventStatus.PROCESSED
    assert len(persisted.attempts) == 1
    assert persisted.attempts[0].failure_reason is None
    assert processor.calls == 1

    with pytest.raises(InvalidTransitionError):
        await process(session_factory, processor)

    assert processor.calls == 1
    persisted_again = await load_event(session_factory)
    assert persisted_again.status is EventStatus.PROCESSED
    assert len(persisted_again.attempts) == 1


async def test_processing_failure_and_attempt_are_persisted(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    await persist_received_event(session_factory)
    processor = RecordingProcessor(RuntimeError("Event processor failed."))

    status = await process(session_factory, processor)

    persisted = await load_event(session_factory)
    assert status is EventStatus.FAILED
    assert persisted.status is EventStatus.FAILED
    assert persisted.failure_reason is not None
    assert persisted.failure_reason.code.value == "processor_error"
    assert persisted.failure_reason.message.value == "Event processor failed."
    assert len(persisted.attempts) == 1
    assert persisted.attempts[0].failure_reason == persisted.failure_reason
    assert processor.calls == 1
