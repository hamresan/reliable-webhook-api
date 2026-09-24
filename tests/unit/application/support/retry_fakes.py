from datetime import datetime

from reliable_webhook_api.application.dto import ProcessEventOutput
from reliable_webhook_api.application.ports import (
    DueRetryReader,
    EventPage,
    EventProcessingRunner,
    EventQuery,
    RetryScheduler,
)
from reliable_webhook_api.domain import EventId, EventStatus, WebhookEvent


class FakeRetryScheduler(RetryScheduler):
    def __init__(self) -> None:
        self.scheduled: list[tuple[EventId, datetime]] = []

    async def schedule(self, event_id: EventId, due_at: datetime) -> None:
        self.scheduled.append((event_id, due_at))


class FakeEventQuery(EventQuery):
    def __init__(self, events: list[WebhookEvent]) -> None:
        self.events = events

    async def get(self, event_id: EventId) -> WebhookEvent | None:
        return next((event for event in self.events if event.id == event_id), None)

    async def page(self, status: EventStatus | None, offset: int, limit: int) -> EventPage:
        matching = [event for event in self.events if status is None or event.status is status]
        return EventPage(items=matching[offset : offset + limit], total=len(matching))


class FakeDueRetryReader(DueRetryReader):
    def __init__(self, events: list[WebhookEvent]) -> None:
        self.events = events

    async def due_retries(self, due_at: datetime, limit: int) -> list[WebhookEvent]:
        matching = [
            event
            for event in self.events
            if event.status is EventStatus.RETRY_SCHEDULED
            and event.next_retry_at is not None
            and event.next_retry_at <= due_at
        ]
        return matching[:limit]


class FakeProcessingRunner(EventProcessingRunner):
    def __init__(self, error: Exception | None = None) -> None:
        self.event_ids: list[EventId] = []
        self.error = error

    async def process(self, event_id: EventId) -> ProcessEventOutput:
        self.event_ids.append(event_id)
        if self.error is not None:
            raise self.error
        return ProcessEventOutput(event_id=event_id.value, status=EventStatus.PROCESSED)
