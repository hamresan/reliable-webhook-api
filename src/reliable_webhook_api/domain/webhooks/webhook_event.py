from dataclasses import dataclass, field
from typing import Any

from reliable_webhook_api.domain.failures import FailureReason
from reliable_webhook_api.domain.identifiers import EventId
from reliable_webhook_api.domain.processing import ProcessingAttempt
from reliable_webhook_api.domain.statuses import EventStatus
from reliable_webhook_api.domain.webhooks.event_type import EventType
from reliable_webhook_api.domain.webhooks.external_event_id import ExternalEventId
from reliable_webhook_api.domain.webhooks.provider_name import ProviderName
from reliable_webhook_api.domain.webhooks.received_at import ReceivedAt


@dataclass(slots=True)
class WebhookEvent:
    id: EventId
    provider: ProviderName
    external_event_id: ExternalEventId
    event_type: EventType
    payload: dict[str, Any]
    status: EventStatus
    received_at: ReceivedAt
    attempts: list[ProcessingAttempt] = field(default_factory=lambda: list[ProcessingAttempt]())
    failure_reason: FailureReason | None = None
