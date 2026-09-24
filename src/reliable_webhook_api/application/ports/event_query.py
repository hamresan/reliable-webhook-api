from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from reliable_webhook_api.domain import EventId, EventStatus, WebhookEvent


@dataclass(frozen=True, slots=True)
class EventPage:
    items: list[WebhookEvent]
    total: int


class EventQuery(Protocol):
    async def get(self, event_id: EventId) -> WebhookEvent | None: ...

    async def page(self, status: EventStatus | None, offset: int, limit: int) -> EventPage: ...

    async def due_retries(self, due_at: datetime, limit: int) -> list[WebhookEvent]: ...
