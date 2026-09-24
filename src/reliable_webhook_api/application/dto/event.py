from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from reliable_webhook_api.domain import EventStatus


@dataclass(frozen=True, slots=True)
class EventInput:
    event_id: UUID
    event_type: str
    occurred_at: datetime
    data: dict[str, Any]


@dataclass(frozen=True, slots=True)
class EventOutput:
    event_id: UUID
    status: EventStatus
