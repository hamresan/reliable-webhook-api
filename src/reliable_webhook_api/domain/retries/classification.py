from dataclasses import dataclass

from reliable_webhook_api.domain.failures import FailureReason


@dataclass(frozen=True, slots=True)
class RetryableFailurePolicy:
    retryable_codes: frozenset[str]

    def is_retryable(self, failure: FailureReason | None) -> bool:
        return failure is not None and failure.code.value in self.retryable_codes
