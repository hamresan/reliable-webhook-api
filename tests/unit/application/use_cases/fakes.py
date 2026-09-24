from datetime import datetime

from reliable_webhook_api.application.ports import (
    Clock,
    EventRepository,
    SignatureVerifier,
)
from reliable_webhook_api.domain import EventId, EventStatus, WebhookEvent


class FakeClock(Clock):
    def __init__(self, current: datetime) -> None:
        self._current = current

    def now(self) -> datetime:
        return self._current


class FakeSignatureVerifier(SignatureVerifier):
    def __init__(self, result: bool) -> None:
        self.result = result
        self.calls: list[tuple[bytes, str]] = []

    def verify(self, payload: bytes, signature: str) -> bool:
        self.calls.append((payload, signature))
        return self.result


class InMemoryEventRepository(EventRepository):
    def __init__(self) -> None:
        self.events: dict[EventId, WebhookEvent] = {}
        self.add_calls = 0

    async def get(self, event_id: EventId) -> WebhookEvent | None:
        return self.events.get(event_id)

    async def add(self, event: WebhookEvent) -> None:
        self.add_calls += 1
        self.events[event.id] = event

    async def save(self, event: WebhookEvent) -> None:
        self.events[event.id] = event

    async def claim_for_processing(self, event_id: EventId) -> WebhookEvent | None:
        event = self.events.get(event_id)
        if event is None or event.status not in {
            EventStatus.RECEIVED,
            EventStatus.RETRY_SCHEDULED,
        }:
            return None
        event.status = EventStatus.PROCESSING
        event.next_retry_at = None
        return event

    async def schedule_retry(self, event_id: EventId, due_at: datetime) -> None:
        event = self.events[event_id]
        event.status = EventStatus.RETRY_SCHEDULED
        event.next_retry_at = due_at

    async def list(self, status: EventStatus | None = None) -> list[WebhookEvent]:
        events = list(self.events.values())
        if status is None:
            return events
        return [event for event in events if event.status is status]
