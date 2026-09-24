from reliable_webhook_api.domain.statuses import EventStatus
from reliable_webhook_api.domain.transitions.errors import InvalidEventTransitionError


class EventTransitionPolicy:
    _allowed: dict[EventStatus, frozenset[EventStatus]] = {
        EventStatus.RECEIVED: frozenset({EventStatus.PROCESSING}),
        EventStatus.PROCESSING: frozenset({EventStatus.PROCESSED, EventStatus.FAILED}),
        EventStatus.FAILED: frozenset({EventStatus.RETRY_SCHEDULED, EventStatus.DEAD_LETTER}),
        EventStatus.RETRY_SCHEDULED: frozenset({EventStatus.PROCESSING}),
        EventStatus.PROCESSED: frozenset(),
        EventStatus.DEAD_LETTER: frozenset(),
    }

    def ensure_allowed(self, current: EventStatus, target: EventStatus) -> None:
        if target not in self._allowed[current]:
            raise InvalidEventTransitionError(current, target)
