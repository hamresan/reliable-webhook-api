from dataclasses import dataclass
from datetime import datetime

from reliable_webhook_api.domain.failures.failure_reason import FailureReason


@dataclass(frozen=True, slots=True)
class ProcessingAttempt:
    number: int
    started_at: datetime
    finished_at: datetime | None = None
    failure_reason: FailureReason | None = None

    def __post_init__(self) -> None:
        if self.number < 1:
            raise ValueError("Processing attempt number must be at least 1.")
        if self.started_at.tzinfo is None:
            raise ValueError("Processing attempt started_at must be timezone-aware.")
        if self.finished_at is not None and self.finished_at.tzinfo is None:
            raise ValueError("Processing attempt finished_at must be timezone-aware.")
        if self.finished_at is not None and self.finished_at < self.started_at:
            raise ValueError("Processing attempt cannot finish before it starts.")
