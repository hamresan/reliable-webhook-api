from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from reliable_webhook_api.domain.events.event_id import EventId
from reliable_webhook_api.domain.events.failure_reason import FailureReason
from reliable_webhook_api.domain.events.processing_attempt import ProcessingAttempt
from reliable_webhook_api.domain.events.status import EventStatus


@dataclass(slots=True)
class WebhookEvent:
    id: EventId
    provider: str
    external_event_id: str
    event_type: str
    payload: dict[str, Any]
    status: EventStatus
    received_at: datetime
    attempts: list[ProcessingAttempt] = field(
        default_factory=lambda: list[ProcessingAttempt]()
    )
    failure_reason: FailureReason | None = None

    def __post_init__(self) -> None:
        if not self.provider.strip():
            raise ValueError("Provider must not be empty.")
        if not self.external_event_id.strip():
            raise ValueError("External event id must not be empty.")
        if not self.event_type.strip():
            raise ValueError("Event type must not be empty.")
        if self.received_at.tzinfo is None:
            raise ValueError("received_at must be timezone-aware.")
