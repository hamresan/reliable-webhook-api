from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from reliable_webhook_api.domain import EventStatus


class WebhookEventRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "event_id": "00000000-0000-0000-0000-000000000001",
                "event_type": "invoice.paid",
                "occurred_at": "2026-09-24T12:00:00Z",
                "data": {"invoice_id": "inv_1"},
            }
        },
    )

    event_id: UUID
    event_type: str = Field(min_length=1)
    occurred_at: datetime
    data: dict[str, Any]


class WebhookEventResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "event_id": "00000000-0000-0000-0000-000000000001",
                "status": "received",
                "duplicate": False,
            }
        }
    )

    event_id: UUID
    status: EventStatus
    duplicate: bool
