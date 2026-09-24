from typing import Protocol

from reliable_webhook_api.domain import WebhookEvent


class EventProcessor(Protocol):
    async def process(self, event: WebhookEvent) -> None: ...
