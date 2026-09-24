from collections.abc import Awaitable, Callable

from reliable_webhook_api.application.ports import EventProcessor
from reliable_webhook_api.domain import WebhookEvent

EventHandler = Callable[[WebhookEvent], Awaitable[None]]


class DeterministicEventProcessor(EventProcessor):
    def __init__(self, handlers: dict[str, EventHandler]) -> None:
        self._handlers = handlers

    async def process(self, event: WebhookEvent) -> None:
        handler = self._handlers.get(event.event_type.value)
        if handler is None:
            raise ValueError(f"Unsupported event type: {event.event_type.value}")
        await handler(event)
