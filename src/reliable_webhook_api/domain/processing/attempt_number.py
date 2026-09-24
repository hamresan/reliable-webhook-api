from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AttemptNumber:
    value: int

    def __post_init__(self) -> None:
        if self.value < 1:
            raise ValueError("Processing attempt number must be at least 1.")
