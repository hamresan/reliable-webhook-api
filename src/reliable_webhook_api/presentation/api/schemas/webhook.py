from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from reliable_webhook_api.domain import EventStatus


class WebhookEventRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: UUID
    event_type: str = Field(min_length=1)
    occurred_at: datetime
    data: dict[str, Any]


class WebhookEventResponse(BaseModel):
    event_id: UUID
    status: EventStatus
    duplicate: bool
