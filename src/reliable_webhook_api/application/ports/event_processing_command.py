from typing import Protocol

from reliable_webhook_api.application.dto import ProcessEventOutput
from reliable_webhook_api.domain import EventId


class EventProcessingCommand(Protocol):
    async def execute(self, event_id: EventId) -> ProcessEventOutput: ...
