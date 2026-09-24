from reliable_webhook_api.domain.processing import AttemptNumber
from reliable_webhook_api.domain.statuses import EventStatus


class RetryNotAllowedError(ValueError):
    def __init__(
        self,
        status: EventStatus,
        attempt_number: AttemptNumber,
    ) -> None:
        super().__init__(
            f"Retry is not allowed for status={status.value}, attempt={attempt_number.value}."
        )
        self.status = status
        self.attempt_number = attempt_number
