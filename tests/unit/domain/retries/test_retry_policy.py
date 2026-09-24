import pytest

from reliable_webhook_api.domain import (
    AttemptNumber,
    EventStatus,
    MaxAttempts,
    RetryNotAllowedError,
    RetryPolicy,
)


def test_retry_is_allowed_for_failed_event_below_max_attempts() -> None:
    RetryPolicy(MaxAttempts(3)).ensure_allowed(
        EventStatus.FAILED,
        AttemptNumber(2),
    )


@pytest.mark.parametrize(
    "status",
    [
        EventStatus.RECEIVED,
        EventStatus.PROCESSING,
        EventStatus.PROCESSED,
        EventStatus.DEAD_LETTER,
    ],
)
def test_retry_is_rejected_for_non_failed_status(status: EventStatus) -> None:
    with pytest.raises(RetryNotAllowedError) as error:
        RetryPolicy(MaxAttempts(3)).ensure_allowed(status, AttemptNumber(1))

    assert error.value.status is status
    assert error.value.attempt_number == AttemptNumber(1)


@pytest.mark.parametrize("attempt", [3, 4])
def test_retry_is_rejected_at_or_above_max_attempts(attempt: int) -> None:
    with pytest.raises(RetryNotAllowedError) as error:
        RetryPolicy(MaxAttempts(3)).ensure_allowed(
            EventStatus.FAILED,
            AttemptNumber(attempt),
        )

    assert error.value.status is EventStatus.FAILED
    assert error.value.attempt_number == AttemptNumber(attempt)


@pytest.mark.parametrize(
    "status",
    [EventStatus.PROCESSED, EventStatus.DEAD_LETTER],
)
def test_terminal_states_never_allow_retry(status: EventStatus) -> None:
    with pytest.raises(RetryNotAllowedError):
        RetryPolicy(MaxAttempts(3)).ensure_allowed(status, AttemptNumber(1))
