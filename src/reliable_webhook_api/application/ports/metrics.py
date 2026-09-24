from typing import Protocol


class Metrics(Protocol):
    def increment(self, name: str) -> None: ...
