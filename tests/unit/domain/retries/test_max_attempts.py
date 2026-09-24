import pytest

from reliable_webhook_api.domain import MaxAttempts


@pytest.mark.parametrize("value", [0, -1])
def test_max_attempts_rejects_values_below_one(value: int) -> None:
    with pytest.raises(ValueError, match="at least 1"):
        MaxAttempts(value)
