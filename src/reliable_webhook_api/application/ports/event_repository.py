from typing import Protocol

from reliable_webhook_api.domain import EventId, WebhookEvent


class EventRepository(Protocol):
    async def get(self, event_id: EventId) -> WebhookEvent | None: ...

    async def add(self, event: WebhookEvent) -> None: ...

    async def save(self, event: WebhookEvent) -> None: ...
