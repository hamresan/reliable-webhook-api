from reliable_webhook_api.application.dto.operations import AttemptOutput, OperationalEventOutput
from reliable_webhook_api.domain import WebhookEvent


class OperationalEventMapper:
    def to_output(self, event: WebhookEvent) -> OperationalEventOutput:
        return OperationalEventOutput(
            event_id=event.id.value,
            event_type=event.event_type.value,
            status=event.status,
            occurred_at=event.occurred_at.value,
            received_at=event.received_at.value,
            attempts=tuple(
                AttemptOutput(
                    number=attempt.number.value,
                    started_at=attempt.period.started_at.value,
                    finished_at=(
                        attempt.period.finished_at.value
                        if attempt.period.finished_at is not None
                        else None
                    ),
                    failure_code=(
                        attempt.failure_reason.code.value
                        if attempt.failure_reason is not None
                        else None
                    ),
                )
                for attempt in event.attempts
            ),
            failure_code=(
                event.failure_reason.code.value if event.failure_reason is not None else None
            ),
            failure_message=(
                event.failure_reason.message.value if event.failure_reason is not None else None
            ),
            next_retry_at=event.next_retry_at,
        )
