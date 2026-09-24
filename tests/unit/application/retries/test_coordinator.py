from datetime import timedelta

from reliable_webhook_api.application.retries import RetryCoordinator
from reliable_webhook_api.domain import (
    EventStatus,
    EventTransitionPolicy,
    ExponentialBackoff,
    MaxAttempts,
    RetryableFailurePolicy,
    RetryPolicy,
)
from tests.unit.application.support import FakeRetryScheduler, build_event
from tests.unit.application.support.event_builder import NOW
from tests.unit.application.use_cases.fakes import FakeClock, InMemoryEventRepository


def build_coordinator(
    repository: InMemoryEventRepository,
    scheduler: FakeRetryScheduler,
) -> RetryCoordinator:
    return RetryCoordinator(
        repository=repository,
        scheduler=scheduler,
        clock=FakeClock(NOW),
        retry_policy=RetryPolicy(MaxAttempts(3)),
        retryable_failures=RetryableFailurePolicy(frozenset({"processor_error"})),
        backoff=ExponentialBackoff(timedelta(seconds=10), timedelta(seconds=60)),
        transition_policy=EventTransitionPolicy(),
    )


async def test_schedule_if_allowed_persists_one_retry() -> None:
    event = build_event()
    repository = InMemoryEventRepository()
    repository.events[event.id] = event
    scheduler = FakeRetryScheduler()

    retry_at = await build_coordinator(repository, scheduler).schedule_if_allowed(event)

    assert retry_at == NOW + timedelta(seconds=10)
    assert event.status is EventStatus.RETRY_SCHEDULED
    assert scheduler.scheduled == [(event.id, retry_at)]


async def test_schedule_if_allowed_leaves_non_retryable_failure_failed() -> None:
    event = build_event(failure_code="validation_error")
    repository = InMemoryEventRepository()
    repository.events[event.id] = event
    scheduler = FakeRetryScheduler()

    retry_at = await build_coordinator(repository, scheduler).schedule_if_allowed(event)

    assert retry_at is None
    assert event.status is EventStatus.FAILED
    assert scheduler.scheduled == []
