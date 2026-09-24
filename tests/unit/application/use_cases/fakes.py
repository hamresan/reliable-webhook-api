from datetime import datetime

from reliable_webhook_api.application.ports import (
    Clock,
    EventRepository,
    SignatureVerifier,
    Transaction,
)
from reliable_webhook_api.domain import EventId, WebhookEvent


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


class FakeTransaction(Transaction):
    async def __aenter__(self) -> "FakeTransaction":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object | None,
    ) -> bool | None:
        return None
