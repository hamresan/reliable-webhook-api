from datetime import UTC, datetime
from uuid import uuid4

import pytest

from reliable_webhook_api.domain import EventId, EventStatus, WebhookEvent


def build_event(**overrides: object) -> WebhookEvent:
    values: dict[str, object] = {
        "id": EventId(uuid4()),
        "provider": "example",
        "external_event_id": "evt_123",
        "event_type": "order.created",
        "payload": {"order_id": "123"},
        "status": EventStatus.RECEIVED,
        "received_at": datetime.now(UTC),
    }
    values.update(overrides)
    return WebhookEvent(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize("field", ["provider", "external_event_id", "event_type"])
@pytest.mark.parametrize("value", ["", "   "])
def test_webhook_event_rejects_empty_required_text(field: str, value: str) -> None:
    with pytest.raises(ValueError):
        build_event(**{field: value})


def test_webhook_event_rejects_naive_received_at() -> None:
    with pytest.raises(ValueError, match="received_at"):
        build_event(received_at=datetime.now())
