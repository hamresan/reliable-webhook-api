from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from reliable_webhook_api.domain import EventStatus


@dataclass(frozen=True, slots=True)
class AttemptOutput:
    number: int
    started_at: datetime
    finished_at: datetime | None
    failure_code: str | None


@dataclass(frozen=True, slots=True)
class OperationalEventOutput:
    event_id: UUID
    event_type: str
    status: EventStatus
    occurred_at: datetime
    received_at: datetime
    attempts: tuple[AttemptOutput, ...]
    failure_code: str | None
    failure_message: str | None
    next_retry_at: datetime | None


@dataclass(frozen=True, slots=True)
class EventPageOutput:
    items: tuple[OperationalEventOutput, ...]
    total: int
    offset: int
    limit: int


@dataclass(frozen=True, slots=True)
class RetryEventOutput:
    event_id: UUID
    status: EventStatus
    retry_at: datetime
