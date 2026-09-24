from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from reliable_webhook_api.application.errors import InvalidTransitionError, NotFoundError
from reliable_webhook_api.application.ports import EventProcessor
from reliable_webhook_api.application.processing import ProcessingFailureMapper
from reliable_webhook_api.application.retries import RetryCoordinator
from reliable_webhook_api.application.use_cases.process_received_event import ProcessReceivedEvent
from reliable_webhook_api.domain import (
    EventId,
    EventStatus,
    EventTransitionPolicy,
    EventType,
    ExponentialBackoff,
    MaxAttempts,
    OccurredAt,
    ReceivedAt,
    RetryableFailurePolicy,
    RetryPolicy,
    WebhookEvent,
)
from tests.support.fake_unit_of_work import FakeUnitOfWork
from tests.unit.application.support import FakeRetryScheduler
from tests.unit.application.use_cases.fakes import FakeClock, InMemoryEventRepository

EVENT_ID = EventId(UUID("00000000-0000-0000-0000-000000000401"))
NOW = datetime(2026, 9, 24, 14, 0, tzinfo=UTC)


class FakeProcessor(EventProcessor):
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.calls: list[WebhookEvent] = []

    async def process(self, event: WebhookEvent) -> None:
        self.calls.append(event)
        if self.error is not None:
            raise self.error


def build_event(status: EventStatus = EventStatus.RECEIVED) -> WebhookEvent:
    return WebhookEvent(
        id=EVENT_ID,
        event_type=EventType("invoice.paid"),
        occurred_at=OccurredAt(NOW),
        data={"invoice_id": "inv-401"},
        status=status,
        received_at=ReceivedAt(NOW),
    )


def build_use_case(
    repository: InMemoryEventRepository,
    processor: FakeProcessor,
    scheduler: FakeRetryScheduler,
) -> ProcessReceivedEvent:
    clock = FakeClock(NOW + timedelta(seconds=1))
    coordinator = RetryCoordinator(
        repository=repository,
        scheduler=scheduler,
        clock=clock,
        retry_policy=RetryPolicy(MaxAttempts(3)),
        retryable_failures=RetryableFailurePolicy(frozenset({"processor_error"})),
        backoff=ExponentialBackoff(timedelta(seconds=10), timedelta(seconds=60)),
        transition_policy=EventTransitionPolicy(),
    )
    return ProcessReceivedEvent(
        repository=repository,
        processor=processor,
        clock=clock,
        unit_of_work=FakeUnitOfWork(),
        transition_policy=EventTransitionPolicy(),
        failure_mapper=ProcessingFailureMapper(),
        retry_coordinator=coordinator,
    )


async def test_processes_received_event_once_and_records_successful_attempt() -> None:
    repository = InMemoryEventRepository()
    repository.events[EVENT_ID] = build_event()
    processor = FakeProcessor()

    result = await build_use_case(repository, processor, FakeRetryScheduler()).execute(EVENT_ID)

    event = repository.events[EVENT_ID]
    assert result.status is EventStatus.PROCESSED
    assert len(processor.calls) == 1
    assert event.status is EventStatus.PROCESSED
    assert len(event.attempts) == 1
    assert event.attempts[0].failure_reason is None


async def test_processor_failure_schedules_one_retry_with_safe_attempt() -> None:
    repository = InMemoryEventRepository()
    repository.events[EVENT_ID] = build_event()
    processor = FakeProcessor(RuntimeError("provider token=secret rejected event"))
    scheduler = FakeRetryScheduler()

    result = await build_use_case(repository, processor, scheduler).execute(EVENT_ID)

    event = repository.events[EVENT_ID]
    assert result.status is EventStatus.RETRY_SCHEDULED
    assert event.failure_reason is not None
    assert event.failure_reason.code.value == "processor_error"
    assert event.failure_reason.message.value == "Event processor failed."
    assert len(event.attempts) == 1
    assert scheduler.scheduled == [(EVENT_ID, NOW + timedelta(seconds=11))]


async def test_missing_event_is_not_processed() -> None:
    repository = InMemoryEventRepository()
    processor = FakeProcessor()

    with pytest.raises(NotFoundError):
        await build_use_case(repository, processor, FakeRetryScheduler()).execute(EVENT_ID)

    assert processor.calls == []


async def test_terminal_event_cannot_be_claimed_or_processed() -> None:
    repository = InMemoryEventRepository()
    repository.events[EVENT_ID] = build_event(EventStatus.PROCESSED)
    processor = FakeProcessor()

    with pytest.raises(InvalidTransitionError):
        await build_use_case(repository, processor, FakeRetryScheduler()).execute(EVENT_ID)

    assert processor.calls == []
