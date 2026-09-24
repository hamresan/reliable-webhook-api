from reliable_webhook_api.application.dto import OperationalEventOutput
from reliable_webhook_api.presentation.api.schemas.operations import (
    AttemptResponse,
    EventResponse,
)


class OperationalResponseMapper:
    @staticmethod
    def to_response(event: OperationalEventOutput) -> EventResponse:
        return EventResponse(
            event_id=event.event_id,
            event_type=event.event_type,
            status=event.status,
            occurred_at=event.occurred_at,
            received_at=event.received_at,
            attempts=[
                AttemptResponse(
                    number=attempt.number,
                    started_at=attempt.started_at,
                    finished_at=attempt.finished_at,
                    failure_code=attempt.failure_code,
                )
                for attempt in event.attempts
            ],
            failure_code=event.failure_code,
            failure_message=event.failure_message,
            next_retry_at=event.next_retry_at,
        )
