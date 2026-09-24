import pytest

from reliable_webhook_api.domain import (
    EventStatus,
    EventTransitionPolicy,
    InvalidEventTransitionError,
)

ALLOWED_TRANSITIONS = {
    (EventStatus.RECEIVED, EventStatus.PROCESSING),
    (EventStatus.PROCESSING, EventStatus.PROCESSED),
    (EventStatus.PROCESSING, EventStatus.FAILED),
    (EventStatus.FAILED, EventStatus.RETRY_SCHEDULED),
    (EventStatus.FAILED, EventStatus.DEAD_LETTER),
    (EventStatus.RETRY_SCHEDULED, EventStatus.PROCESSING),
}


@pytest.mark.parametrize(("current", "target"), sorted(ALLOWED_TRANSITIONS))
def test_policy_allows_valid_transition(current: EventStatus, target: EventStatus) -> None:
    EventTransitionPolicy().ensure_allowed(current, target)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (current, target)
        for current in EventStatus
        for target in EventStatus
        if (current, target) not in ALLOWED_TRANSITIONS
    ],
)
def test_policy_rejects_invalid_transition(current: EventStatus, target: EventStatus) -> None:
    with pytest.raises(InvalidEventTransitionError) as error:
        EventTransitionPolicy().ensure_allowed(current, target)

    assert error.value.current is current
    assert error.value.target is target
