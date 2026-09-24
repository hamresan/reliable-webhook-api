from datetime import datetime

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
from reliable_webhook_api.infrastructure.persistence.models import (
    EventModel,
    ProcessingAttemptModel,
)


class EventPersistenceMapper:
    @staticmethod
    def to_model(event: WebhookEvent, updated_at: datetime) -> EventModel:
        return EventModel(
            event_id=event.id.value,
            event_type=event.event_type.value,
            payload=event.data,
            occurred_at=event.occurred_at.value,
            received_at=event.received_at.value,
            status=event.status.value,
            failure_code=event.failure_reason.code.value if event.failure_reason else None,
            failure_message=event.failure_reason.message.value if event.failure_reason else None,
            next_retry_at=event.next_retry_at,
            updated_at=updated_at,
            attempts=[
                EventPersistenceMapper.attempt_to_model(attempt) for attempt in event.attempts
            ],
        )

    @staticmethod
    def to_domain(model: EventModel) -> WebhookEvent:
        return WebhookEvent(
            id=EventId(model.event_id),
            event_type=EventType(model.event_type),
            occurred_at=OccurredAt(model.occurred_at),
            data=model.payload,
            status=EventStatus(model.status),
            received_at=ReceivedAt(model.received_at),
            attempts=[
                EventPersistenceMapper.attempt_to_domain(attempt) for attempt in model.attempts
            ],
            failure_reason=EventPersistenceMapper.failure_reason(
                model.failure_code,
                model.failure_message,
            ),
            next_retry_at=model.next_retry_at,
        )

    @staticmethod
    def attempt_to_model(attempt: ProcessingAttempt) -> ProcessingAttemptModel:
        return ProcessingAttemptModel(
            number=attempt.number.value,
            started_at=attempt.period.started_at.value,
            finished_at=attempt.period.finished_at.value if attempt.period.finished_at else None,
            failure_code=attempt.failure_reason.code.value if attempt.failure_reason else None,
            failure_message=attempt.failure_reason.message.value
            if attempt.failure_reason
            else None,
        )

    @staticmethod
    def attempt_to_domain(model: ProcessingAttemptModel) -> ProcessingAttempt:
        finished_at = (
            ProcessingTimestamp(model.finished_at) if model.finished_at is not None else None
        )
        return ProcessingAttempt(
            number=AttemptNumber(model.number),
            period=ProcessingPeriod(
                started_at=ProcessingTimestamp(model.started_at),
                finished_at=finished_at,
            ),
            failure_reason=EventPersistenceMapper.failure_reason(
                model.failure_code,
                model.failure_message,
            ),
        )

    @staticmethod
    def failure_reason(code: str | None, message: str | None) -> FailureReason | None:
        if code is None or message is None:
            return None
        return FailureReason(FailureCode(code), FailureMessage(message))
