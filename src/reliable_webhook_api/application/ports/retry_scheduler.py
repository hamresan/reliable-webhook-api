from datetime import datetime
from typing import Protocol

from reliable_webhook_api.domain import EventId


class RetryScheduler(Protocol):
    async def schedule(self, event_id: EventId, due_at: datetime) -> None: ...
