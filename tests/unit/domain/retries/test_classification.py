from reliable_webhook_api.domain import (
    FailureCode,
    FailureMessage,
    FailureReason,
    RetryableFailurePolicy,
)


def test_retryable_failure_classification_is_explicit() -> None:
    policy = RetryableFailurePolicy(frozenset({"processor_error"}))

    assert policy.is_retryable(
        FailureReason(FailureCode("processor_error"), FailureMessage("safe"))
    )
    assert not policy.is_retryable(
        FailureReason(FailureCode("validation_error"), FailureMessage("safe"))
    )
    assert not policy.is_retryable(None)
