from reliable_webhook_api.application.dto import ProcessEventOutput
from reliable_webhook_api.application.ports import EventProcessingCommand
from reliable_webhook_api.domain import EventId, EventStatus


class FakeProcessingCommand(EventProcessingCommand):
    def __init__(self) -> None:
        self.event_ids: list[EventId] = []

    async def execute(self, event_id: EventId) -> ProcessEventOutput:
        self.event_ids.append(event_id)
        return ProcessEventOutput(event_id=event_id.value, status=EventStatus.PROCESSED)
