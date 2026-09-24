from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FailureReason:
    code: str
    message: str

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("Failure reason code must not be empty.")
        if not self.message.strip():
            raise ValueError("Failure reason message must not be empty.")
