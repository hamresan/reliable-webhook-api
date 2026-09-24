from datetime import datetime

from reliable_webhook_api.application.ports import RetryScheduler
from reliable_webhook_api.domain import EventId


class InProcessRetryScheduler(RetryScheduler):
    def __init__(self) -> None:
        self._scheduled: list[tuple[EventId, datetime]] = []

    async def schedule(self, event_id: EventId, due_at: datetime) -> None:
        self._scheduled.append((event_id, due_at))

    @property
    def scheduled(self) -> tuple[tuple[EventId, datetime], ...]:
        return tuple(self._scheduled)
