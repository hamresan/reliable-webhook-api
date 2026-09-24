from reliable_webhook_api.domain.events.status import EventStatus


class InvalidEventTransitionError(ValueError):
    def __init__(self, current: EventStatus, target: EventStatus) -> None:
        super().__init__(f"Invalid event status transition: {current.value} -> {target.value}.")
        self.current = current
        self.target = target
