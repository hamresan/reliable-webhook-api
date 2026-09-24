from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class OccurredAt:
    value: datetime

    def __post_init__(self) -> None:
        if self.value.tzinfo is None:
            raise ValueError("Occurred timestamp must be timezone-aware.")
