import pytest

from reliable_webhook_api.domain import FailureReason


@pytest.mark.parametrize("value", ["", "   "])
def test_failure_reason_rejects_empty_code(value: str) -> None:
    with pytest.raises(ValueError, match="code"):
        FailureReason(code=value, message="Temporary failure")


@pytest.mark.parametrize("value", ["", "   "])
def test_failure_reason_rejects_empty_message(value: str) -> None:
    with pytest.raises(ValueError, match="message"):
        FailureReason(code="temporary", message=value)
