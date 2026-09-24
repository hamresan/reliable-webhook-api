from datetime import timedelta

from reliable_webhook_api.application.use_cases import ProcessDueRetries
from reliable_webhook_api.domain import EventStatus
from tests.unit.application.support import (
    FakeDueRetryReader,
    FakeProcessingRunner,
    build_event,
)
from tests.unit.application.support.event_builder import NOW
from tests.unit.application.use_cases.fakes import FakeClock


async def test_processes_only_due_retry_events() -> None:
    due = build_event(status=EventStatus.RETRY_SCHEDULED)
    due.next_retry_at = NOW
    future = build_event(status=EventStatus.RETRY_SCHEDULED)
    future.next_retry_at = NOW + timedelta(minutes=1)
    runner = FakeProcessingRunner()

    count = await ProcessDueRetries(
        FakeDueRetryReader([due, future]),
        runner,
        FakeClock(NOW),
    ).execute()

    assert count == 1
    assert runner.event_ids == [due.id]
