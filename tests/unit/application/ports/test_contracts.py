from datetime import UTC, datetime
from uuid import uuid4

from reliable_webhook_api.application.ports import (
    Clock,
    EventProcessor,
    EventRepository,
    SignatureVerifier,
    Transaction,
)
from reliable_webhook_api.domain import EventId, WebhookEvent


class StubClock(Clock):
    def now(self) -> datetime:
        return datetime.now(UTC)


class StubSignatureVerifier(SignatureVerifier):
    def verify(self, payload: bytes, signature: str) -> bool:
        return bool(payload and signature)


class StubRepository(EventRepository):
    async def get(self, event_id: EventId) -> WebhookEvent | None:
        return None

    async def add(self, event: WebhookEvent) -> None:
        return None

    async def save(self, event: WebhookEvent) -> None:
        return None


class StubProcessor(EventProcessor):
    async def process(self, event: WebhookEvent) -> None:
        return None


class StubTransaction(Transaction):
    async def __aenter__(self) -> "StubTransaction":
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> bool | None:
        return None


def test_ports_accept_explicit_implementations() -> None:
    assert isinstance(StubClock(), Clock) is False
    assert StubSignatureVerifier().verify(b"payload", "signature")
    assert StubRepository() is not None
    assert StubProcessor() is not None
    assert StubTransaction() is not None
