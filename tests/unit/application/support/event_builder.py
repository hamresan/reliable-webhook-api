from datetime import UTC, datetime
from uuid import UUID

from reliable_webhook_api.domain import (
    AttemptNumber,
    EventId,
    EventStatus,
    EventType,
    FailureCode,
    FailureMessage,
    FailureReason,
    OccurredAt,
    ProcessingAttempt,
    ProcessingPeriod,
    ProcessingTimestamp,
    ReceivedAt,
    WebhookEvent,
)

NOW = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)


def build_event(
    status: EventStatus = EventStatus.FAILED,
    failure_code: str = "processor_error",
    attempts: int = 1,
) -> WebhookEvent:
    processing_attempts = [
        ProcessingAttempt(
            number=AttemptNumber(number),
            period=ProcessingPeriod(
                started_at=ProcessingTimestamp(NOW),
                finished_at=ProcessingTimestamp(NOW),
            ),
            failure_reason=FailureReason(
                FailureCode(failure_code),
                FailureMessage("sanitized failure"),
            ),
        )
        for number in range(1, attempts + 1)
    ]
    return WebhookEvent(
        id=EventId(UUID("00000000-0000-0000-0000-000000000505")),
        event_type=EventType("invoice.paid"),
        occurred_at=OccurredAt(NOW),
        data={"invoice_id": "inv-505"},
        status=status,
        received_at=ReceivedAt(NOW),
        attempts=processing_attempts,
        failure_reason=FailureReason(
            FailureCode(failure_code),
            FailureMessage("sanitized failure"),
        ),
    )
