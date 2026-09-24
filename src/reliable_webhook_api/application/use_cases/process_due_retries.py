from reliable_webhook_api.application.ports import Clock, EventQuery
from reliable_webhook_api.application.use_cases.process_received_event import ProcessReceivedEvent


class ProcessDueRetries:
    def __init__(self, query: EventQuery, processor: ProcessReceivedEvent, clock: Clock) -> None:
        self._query = query
        self._processor = processor
        self._clock = clock

    async def execute(self, limit: int = 100) -> int:
        events = await self._query.due_retries(self._clock.now(), limit)
        for event in events:
            await self._processor.execute(event.id)
        return len(events)
