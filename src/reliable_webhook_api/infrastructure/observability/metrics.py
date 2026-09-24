from collections import Counter
from functools import lru_cache

from reliable_webhook_api.application.ports import Metrics


class InMemoryMetrics(Metrics):
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
