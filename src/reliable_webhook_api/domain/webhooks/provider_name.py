from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProviderName:
    value: str

    def __post_init__(self) -> None:
        if not self.value.strip():
            raise ValueError("Provider name must not be empty.")
