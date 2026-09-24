from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FailureCode:
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("Failure code must not be empty.")
