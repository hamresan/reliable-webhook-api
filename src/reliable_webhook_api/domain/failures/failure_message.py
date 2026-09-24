from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FailureMessage:
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("Failure message must not be empty.")
