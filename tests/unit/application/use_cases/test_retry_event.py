from datetime import timedelta

import pytest

from reliable_webhook_api.application.errors import InvalidTransitionError, NotFoundError
from reliable_webhook_api.application.use_cases import RetryEvent
from reliable_webhook_api.domain import (
    EventId,
    EventStatus,
    EventTransitionPolicy,
    ExponentialBackoff,
    MaxAttempts,
    RetryableFailurePolicy,
    RetryPolicy,
)
from tests.support.fake_unit_of_work import FakeUnitOfWork
from tests.unit.application.support import FakeRetryScheduler, build_event
from tests.unit.application.support.event_builder import NOW
from tests.unit.application.use_cases.fakes import FakeClock, InMemoryEventRepository


def build_use_case(
    repository: InMemoryEventRepository,
    scheduler: FakeRetryScheduler,
    max_attempts: int = 3,
) -> RetryEvent:
    return RetryEvent(
        repository=repository,
        scheduler=scheduler,
        clock=FakeClock(NOW),
        unit_of_work=FakeUnitOfWork(),
        retry_policy=RetryPolicy(MaxAttempts(max_attempts)),
        retryable_failures=RetryableFailurePolicy(frozenset({"processor_error"})),
        backoff=ExponentialBackoff(timedelta(seconds=10), timedelta(seconds=60)),
        transition_policy=EventTransitionPolicy(),
    )


async def test_failed_retryable_event_is_scheduled_with_backoff() -> None:
    event = build_event()
    repository = InMemoryEventRepository()
    repository.events[event.id] = event
    scheduler = FakeRetryScheduler()

    result = await build_use_case(repository, scheduler).execute(event.id)

    assert result.status is EventStatus.RETRY_SCHEDULED
    assert result.retry_at == NOW + timedelta(seconds=10)
    assert event.next_retry_at == result.retry_at
    assert scheduler.scheduled == [(event.id, result.retry_at)]


async def test_non_retryable_failure_is_rejected() -> None:
    event = build_event(failure_code="validation_error")
    repository = InMemoryEventRepository()
    repository.events[event.id] = event

    with pytest.raises(InvalidTransitionError, match="not retryable"):
        await build_use_case(repository, FakeRetryScheduler()).execute(event.id)


async def test_max_attempts_is_enforced() -> None:
    event = build_event(attempts=3)
    repository = InMemoryEventRepository()
    repository.events[event.id] = event

    with pytest.raises(InvalidTransitionError):
        await build_use_case(repository, FakeRetryScheduler(), max_attempts=3).execute(event.id)


async def test_terminal_event_is_rejected() -> None:
    event = build_event(status=EventStatus.PROCESSED)
    repository = InMemoryEventRepository()
    repository.events[event.id] = event

    with pytest.raises(InvalidTransitionError):
        await build_use_case(repository, FakeRetryScheduler()).execute(event.id)


async def test_missing_event_is_rejected() -> None:
    repository = InMemoryEventRepository()

    with pytest.raises(NotFoundError):
        await build_use_case(repository, FakeRetryScheduler()).execute(
            EventId(build_event().id.value)
        )
