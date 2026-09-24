from datetime import UTC, datetime
from uuid import uuid4

from reliable_webhook_api.domain import (
    EventId,
    EventStatus,
    EventType,
    ExternalEventId,
    ProviderName,
    ReceivedAt,
    WebhookEvent,
)


def build_event() -> WebhookEvent:
    return WebhookEvent(
        id=EventId(uuid4()),
        provider=ProviderName("example"),
        external_event_id=ExternalEventId("evt_123"),
        event_type=EventType("order.created"),
        payload={"order_id": "123"},
        status=EventStatus.RECEIVED,
        received_at=ReceivedAt(datetime.now(UTC)),
    )


def test_webhook_event_accepts_valid_domain_values() -> None:
    event = build_event()

    assert event.status is EventStatus.RECEIVED
    assert event.attempts == []
    assert event.failure_reason is None
