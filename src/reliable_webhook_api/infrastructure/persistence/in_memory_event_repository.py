from reliable_webhook_api.application.ports import EventRepository
from reliable_webhook_api.domain import EventId, WebhookEvent


class InMemoryEventRepository(EventRepository):
    def __init__(self) -> None:
        self._events: dict[EventId, WebhookEvent] = {}

    async def get(self, event_id: EventId) -> WebhookEvent | None:
        return self._events.get(event_id)

    async def add(self, event: WebhookEvent) -> None:
        self._events[event.id] = event

    async def save(self, event: WebhookEvent) -> None:
        self._events[event.id] = event
