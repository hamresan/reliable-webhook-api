from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EventType:
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("Event type must not be empty.")
