from dataclasses import dataclass

from reliable_webhook_api.domain.failures import FailureReason
from reliable_webhook_api.domain.processing.attempt_number import AttemptNumber
from reliable_webhook_api.domain.processing.processing_period import ProcessingPeriod


@dataclass(frozen=True, slots=True)
class ProcessingAttempt:
    number: AttemptNumber
    period: ProcessingPeriod
    failure_reason: FailureReason | None = None
