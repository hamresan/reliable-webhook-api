from reliable_webhook_api.application.dto import OperationalEventOutput


class OperationalResponseMapper:
    @staticmethod
    def to_dict(event: OperationalEventOutput) -> dict[str, object]:
        return {
            "event_id": str(event.event_id),
            "event_type": event.event_type,
            "status": event.status.value,
            "occurred_at": event.occurred_at.isoformat(),
            "received_at": event.received_at.isoformat(),
            "attempts": [
                {
                    "number": attempt.number,
                    "started_at": attempt.started_at.isoformat(),
                    "finished_at": (
                        attempt.finished_at.isoformat() if attempt.finished_at is not None else None
                    ),
                    "failure_code": attempt.failure_code,
                }
                for attempt in event.attempts
            ],
            "failure_code": event.failure_code,
            "failure_message": event.failure_message,
            "next_retry_at": (
                event.next_retry_at.isoformat() if event.next_retry_at is not None else None
            ),
        }
