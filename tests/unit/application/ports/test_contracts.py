from datetime import UTC, datetime
from types import TracebackType

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

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        return None


def test_ports_can_be_implemented_explicitly() -> None:
    clock: Clock = StubClock()
    verifier: SignatureVerifier = StubSignatureVerifier()
    repository: EventRepository = StubRepository()
    processor: EventProcessor = StubProcessor()
    transaction: Transaction = StubTransaction()

    assert clock.now().tzinfo is not None
    assert verifier.verify(b"payload", "signature")
    assert repository is not None
    assert processor is not None
    assert transaction is not None
