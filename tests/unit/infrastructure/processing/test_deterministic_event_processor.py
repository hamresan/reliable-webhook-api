from datetime import UTC, datetime
from uuid import UUID

import pytest

from reliable_webhook_api.domain import (
    EventId,
    EventStatus,
    EventType,
    OccurredAt,
    ReceivedAt,
    WebhookEvent,
)
from reliable_webhook_api.infrastructure.processing import DeterministicEventProcessor

NOW = datetime(2026, 9, 24, 14, 0, tzinfo=UTC)


def build_event(event_type: str = "invoice.paid") -> WebhookEvent:
    return WebhookEvent(
        id=EventId(UUID("00000000-0000-0000-0000-000000000402")),
        event_type=EventType(event_type),
        occurred_at=OccurredAt(NOW),
        data={"invoice_id": "inv-402"},
        status=EventStatus.RECEIVED,
        received_at=ReceivedAt(NOW),
    )


async def test_dispatches_event_to_matching_handler() -> None:
    handled: list[WebhookEvent] = []

    async def handle(event: WebhookEvent) -> None:
        handled.append(event)

    event = build_event()
    processor = DeterministicEventProcessor({"invoice.paid": handle})

    await processor.process(event)

    assert handled == [event]


async def test_rejects_unsupported_event_type_without_calling_handler() -> None:
    handled: list[WebhookEvent] = []

    async def handle(event: WebhookEvent) -> None:
        handled.append(event)

    processor = DeterministicEventProcessor({"invoice.paid": handle})

    with pytest.raises(ValueError, match="Unsupported event type: customer.created"):
        await processor.process(build_event("customer.created"))

    assert handled == []
