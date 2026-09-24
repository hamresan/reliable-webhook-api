from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MaxAttempts:
    value: int

    def __post_init__(self) -> None:
        if self.value < 1:
            raise ValueError("Maximum attempts must be at least 1.")
