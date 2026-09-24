from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExternalEventId:
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("External event id must not be empty.")
