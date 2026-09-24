from dataclasses import dataclass
from uuid import UUID

from reliable_webhook_api.domain import EventStatus


@dataclass(frozen=True, slots=True)
class ProcessEventOutput:
    event_id: UUID
    status: EventStatus
