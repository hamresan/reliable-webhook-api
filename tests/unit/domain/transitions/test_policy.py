import pytest

from reliable_webhook_api.domain import (
    EventStatus,
    EventTransitionPolicy,
    InvalidEventTransitionError,
)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (EventStatus.RECEIVED, EventStatus.PROCESSING),
        (EventStatus.PROCESSING, EventStatus.PROCESSED),
        (EventStatus.PROCESSING, EventStatus.FAILED),
        (EventStatus.FAILED, EventStatus.PROCESSING),
        (EventStatus.FAILED, EventStatus.DEAD_LETTER),
    ],
)
def test_policy_allows_valid_transition(current: EventStatus, target: EventStatus) -> None:
    EventTransitionPolicy().ensure_allowed(current, target)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (current, target)
        for current in EventStatus
        for target in EventStatus
        if (current, target)
        not in {
            (EventStatus.RECEIVED, EventStatus.PROCESSING),
            (EventStatus.PROCESSING, EventStatus.PROCESSED),
            (EventStatus.PROCESSING, EventStatus.FAILED),
            (EventStatus.FAILED, EventStatus.PROCESSING),
            (EventStatus.FAILED, EventStatus.DEAD_LETTER),
        }
    ],
)
def test_policy_rejects_invalid_transition(current: EventStatus, target: EventStatus) -> None:
    with pytest.raises(InvalidEventTransitionError) as error:
        EventTransitionPolicy().ensure_allowed(current, target)

    assert error.value.current is current
    assert error.value.target is target
