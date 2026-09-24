from dataclasses import dataclass
from datetime import timedelta

from reliable_webhook_api.domain.processing import AttemptNumber


@dataclass(frozen=True, slots=True)
class ExponentialBackoff:
    base_delay: timedelta
    max_delay: timedelta

    def __post_init__(self) -> None:
        if self.base_delay <= timedelta(0):
            raise ValueError("Base retry delay must be positive.")
        if self.max_delay < self.base_delay:
            raise ValueError("Maximum retry delay must not be smaller than base delay.")

    def delay_for(self, attempt_number: AttemptNumber) -> timedelta:
        multiplier = 2 ** (attempt_number.value - 1)
        return min(self.base_delay * multiplier, self.max_delay)
