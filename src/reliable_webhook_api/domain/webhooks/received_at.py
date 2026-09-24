from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ReceivedAt:
    value: datetime

    def __post_init__(self) -> None:
        if self.value.tzinfo is None:
            raise ValueError("Received timestamp must be timezone-aware.")
