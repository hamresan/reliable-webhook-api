from dataclasses import dataclass

from reliable_webhook_api.domain.processing.processing_timestamp import ProcessingTimestamp


@dataclass(frozen=True, slots=True)
class ProcessingPeriod:
    started_at: ProcessingTimestamp
    finished_at: ProcessingTimestamp | None = None

    def __post_init__(self) -> None:
        if self.finished_at is not None and self.finished_at.value < self.started_at.value:
            raise ValueError("Processing attempt cannot finish before it starts.")
