from reliable_webhook_api.domain.processing import AttemptNumber
from reliable_webhook_api.domain.retries.errors import RetryNotAllowedError
from reliable_webhook_api.domain.retries.max_attempts import MaxAttempts
from reliable_webhook_api.domain.statuses import EventStatus


class RetryPolicy:
    def __init__(self, max_attempts: MaxAttempts) -> None:
        self._max_attempts = max_attempts

    def ensure_allowed(
        self,
        status: EventStatus,
        attempt_number: AttemptNumber,
    ) -> None:
        if status is not EventStatus.FAILED:
            raise RetryNotAllowedError(status, attempt_number)

        if attempt_number.value >= self._max_attempts.value:
            raise RetryNotAllowedError(status, attempt_number)
