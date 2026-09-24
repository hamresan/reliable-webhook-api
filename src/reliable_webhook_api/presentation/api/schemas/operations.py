from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from reliable_webhook_api.domain import EventStatus


class AttemptResponse(BaseModel):
    number: int
    started_at: datetime
    finished_at: datetime | None
    failure_code: str | None


class EventResponse(BaseModel):
    event_id: UUID
    event_type: str
    status: EventStatus
    occurred_at: datetime
    received_at: datetime
    attempts: list[AttemptResponse]
    failure_code: str | None
    failure_message: str | None
    next_retry_at: datetime | None


class EventListResponse(BaseModel):
    items: list[EventResponse]
    total: int
    offset: int
    limit: int


class RetryResponse(BaseModel):
    event_id: UUID
    status: EventStatus
    retry_at: datetime
