from dataclasses import dataclass

from reliable_webhook_api.domain.failures.failure_code import FailureCode
from reliable_webhook_api.domain.failures.failure_message import FailureMessage


@dataclass(frozen=True, slots=True)
class FailureReason:
    code: FailureCode
    message: FailureMessage
