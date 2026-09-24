import pytest

from reliable_webhook_api.domain import FailureCode, FailureMessage, FailureReason


@pytest.mark.parametrize("value", ["", "   "])
def test_failure_code_rejects_empty_value(value: str) -> None:
    with pytest.raises(ValueError, match="code"):
        FailureCode(value)


@pytest.mark.parametrize("value", ["", "   "])
def test_failure_message_rejects_empty_value(value: str) -> None:
    with pytest.raises(ValueError, match="message"):
        FailureMessage(value)


def test_failure_reason_composes_valid_domain_values() -> None:
    reason = FailureReason(
        code=FailureCode("temporary"),
        message=FailureMessage("Temporary failure"),
    )

    assert reason.code == FailureCode("temporary")
    assert reason.message == FailureMessage("Temporary failure")
