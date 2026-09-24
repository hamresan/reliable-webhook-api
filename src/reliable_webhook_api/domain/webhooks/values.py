from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ProviderName:
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("Provider name must not be empty.")


@dataclass(frozen=True, slots=True)
class ExternalEventId:
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("External event id must not be empty.")


@dataclass(frozen=True, slots=True)
class EventType:
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("Event type must not be empty.")


@dataclass(frozen=True, slots=True)
class ReceivedAt:
    value: datetime

    def __post_init__(self) -> None:
        if self.value.tzinfo is None:
            raise ValueError("Received timestamp must be timezone-aware.")
