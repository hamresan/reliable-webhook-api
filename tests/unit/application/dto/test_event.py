from datetime import UTC, datetime
from uuid import uuid4

from reliable_webhook_api.application.dto import EventInput, EventOutput
from reliable_webhook_api.domain import EventStatus


def test_event_dtos_use_application_and_domain_types_only() -> None:
    event_id = uuid4()
    occurred_at = datetime.now(UTC)

    input_dto = EventInput(
        event_id=event_id,
        event_type="invoice.paid",
        occurred_at=occurred_at,
        data={"invoice_id": "inv_1"},
    )
    output_dto = EventOutput(event_id=event_id, status=EventStatus.RECEIVED)

    assert input_dto.occurred_at == occurred_at
    assert output_dto.status is EventStatus.RECEIVED
