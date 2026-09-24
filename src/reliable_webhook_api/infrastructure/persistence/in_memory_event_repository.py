from datetime import datetime

from reliable_webhook_api.application.ports import EventRepository
from reliable_webhook_api.domain import EventId, EventStatus, WebhookEvent


class InMemoryEventRepository(EventRepository):
    def __init__(self) -> None:
        self._events: dict[EventId, WebhookEvent] = {}

    async def get(self, event_id: EventId) -> WebhookEvent | None:
        return self._events.get(event_id)

    async def add(self, event: WebhookEvent) -> None:
        self._events[event.id] = event

    async def save(self, event: WebhookEvent) -> None:
        self._events[event.id] = event

    async def claim_for_processing(self, event_id: EventId) -> WebhookEvent | None:
        event = self._events.get(event_id)
        if event is None or event.status not in {
            EventStatus.RECEIVED,
            EventStatus.RETRY_SCHEDULED,
        }:
            return None
        event.status = EventStatus.PROCESSING
        event.next_retry_at = None
        return event

    async def schedule_retry(self, event_id: EventId, due_at: datetime) -> None:
        event = self._events[event_id]
        event.status = EventStatus.RETRY_SCHEDULED
        event.next_retry_at = due_at

    async def list(self, status: EventStatus | None = None) -> list[WebhookEvent]:
        events = list(self._events.values())
        if status is None:
            return events
        return [event for event in events if event.status is status]

    def count(self) -> int:
        return len(self._events)

    def is_empty(self) -> bool:
        return not self._events
