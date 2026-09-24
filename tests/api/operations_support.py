from datetime import UTC, datetime
from uuid import UUID

from reliable_webhook_api.application.dto import (
    EventPageOutput,
    OperationalEventOutput,
    RetryEventOutput,
)
from reliable_webhook_api.application.errors import InvalidTransitionError, NotFoundError
from reliable_webhook_api.domain import EventStatus

EVENT_ID = UUID("00000000-0000-0000-0000-000000000507")
NOW = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)


def event_output(status: EventStatus = EventStatus.FAILED) -> OperationalEventOutput:
    return OperationalEventOutput(
        event_id=EVENT_ID,
        event_type="invoice.paid",
        status=status,
        occurred_at=NOW,
        received_at=NOW,
        attempts=(),
        failure_code="processor_error" if status is EventStatus.FAILED else None,
        failure_message="Event processor failed." if status is EventStatus.FAILED else None,
        next_retry_at=None,
    )


class StubGetEvent:
    def __init__(self, missing: bool = False) -> None:
        self._missing = missing

    async def execute(self, event_id: object) -> OperationalEventOutput:
        if self._missing:
            raise NotFoundError("missing")
        return event_output()


class StubListEvents:
    async def execute(
        self,
        status: EventStatus | None,
        offset: int,
        limit: int,
    ) -> EventPageOutput:
        item = event_output(status or EventStatus.FAILED)
        return EventPageOutput(items=(item,), total=1, offset=offset, limit=limit)


class StubRetryEvent:
    def __init__(self, error: Exception | None = None) -> None:
        self._error = error

    async def execute(self, event_id: object) -> RetryEventOutput:
        if self._error is not None:
            raise self._error
        return RetryEventOutput(
            event_id=EVENT_ID,
            status=EventStatus.RETRY_SCHEDULED,
            retry_at=NOW,
        )


def terminal_retry_error() -> InvalidTransitionError:
    return InvalidTransitionError("Retry is not allowed for terminal event.")
