from collections import Counter
from functools import lru_cache
from typing import Protocol


class MetricsPort(Protocol):
    def increment(self, name: str) -> None: ...


class InMemoryMetrics(MetricsPort):
    """Minimal replaceable metrics hook suitable for local and test use."""

    def __init__(self) -> None:
        self._counts: Counter[str] = Counter()

    def increment(self, name: str) -> None:
        self._counts[name] += 1

    def value(self, name: str) -> int:
        return self._counts[name]


@lru_cache
def get_metrics() -> InMemoryMetrics:
    return InMemoryMetrics()
