from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from reliable_webhook_api.application.errors import NotFoundError
from reliable_webhook_api.application.ports import EventProcessor
from reliable_webhook_api.application.processing import ProcessingFailureMapper
from reliable_webhook_api.application.use_cases.process_received_event import ProcessReceivedEvent
from reliable_webhook_api.domain import (
    EventId,
    EventStatus,
    EventTransitionPolicy,
    EventType,
    OccurredAt,
    ReceivedAt,
    WebhookEvent,
)
from tests.support.fake_unit_of_work import FakeUnitOfWork
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


async def test_processes_received_event_once_and_records_successful_attempt() -> None:
    repository = InMemoryEventRepository()
    repository.events[EVENT_ID] = build_event()
    processor = FakeProcessor()
    use_case = ProcessReceivedEvent(
        repository,
        processor,
        FakeClock(NOW + timedelta(seconds=1)),
        FakeUnitOfWork(),
        EventTransitionPolicy(),
        ProcessingFailureMapper(),
    )

    result = await use_case.execute(EVENT_ID)

    event = repository.events[EVENT_ID]
    assert result.status is EventStatus.PROCESSED
    assert len(processor.calls) == 1
    assert event.status is EventStatus.PROCESSED
    assert len(event.attempts) == 1
    assert event.attempts[0].failure_reason is None


async def test_processor_failure_marks_failed_and_records_safe_attempt() -> None:
    repository = InMemoryEventRepository()
    repository.events[EVENT_ID] = build_event()
    processor = FakeProcessor(RuntimeError("downstream rejected event"))
    use_case = ProcessReceivedEvent(
        repository,
        processor,
        FakeClock(NOW + timedelta(seconds=1)),
        FakeUnitOfWork(),
        EventTransitionPolicy(),
        ProcessingFailureMapper(),
    )

    result = await use_case.execute(EVENT_ID)

    event = repository.events[EVENT_ID]
    assert result.status is EventStatus.FAILED
    assert event.failure_reason is not None
    assert event.failure_reason.code.value == "processor_error"
    assert len(event.attempts) == 1
    assert event.attempts[0].failure_reason == event.failure_reason


async def test_missing_event_is_not_processed() -> None:
    repository = InMemoryEventRepository()
    processor = FakeProcessor()
    use_case = ProcessReceivedEvent(
        repository,
        processor,
        FakeClock(NOW),
        FakeUnitOfWork(),
        EventTransitionPolicy(),
        ProcessingFailureMapper(),
    )

    with pytest.raises(NotFoundError):
        await use_case.execute(EVENT_ID)

    assert processor.calls == []
