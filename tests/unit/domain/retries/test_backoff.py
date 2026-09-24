from datetime import timedelta

import pytest

from reliable_webhook_api.domain import AttemptNumber, ExponentialBackoff


def test_exponential_backoff_grows_and_is_bounded() -> None:
    policy = ExponentialBackoff(timedelta(seconds=10), timedelta(seconds=25))

    assert policy.delay_for(AttemptNumber(1)) == timedelta(seconds=10)
    assert policy.delay_for(AttemptNumber(2)) == timedelta(seconds=20)
    assert policy.delay_for(AttemptNumber(3)) == timedelta(seconds=25)


@pytest.mark.parametrize(
    ("base", "maximum"),
    [
        (timedelta(0), timedelta(seconds=1)),
        (timedelta(seconds=2), timedelta(seconds=1)),
    ],
)
def test_exponential_backoff_rejects_invalid_configuration(
    base: timedelta,
    maximum: timedelta,
) -> None:
    with pytest.raises(ValueError):
        ExponentialBackoff(base, maximum)
