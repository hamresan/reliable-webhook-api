from reliable_webhook_api.application.ports import (
    Clock,
    DueRetryReader,
    EventProcessingRunner,
)


class ProcessDueRetries:
    def __init__(
        self,
        reader: DueRetryReader,
        runner: EventProcessingRunner,
        clock: Clock,
    ) -> None:
        self._reader = reader
        self._runner = runner
        self._clock = clock

    async def execute(self, limit: int = 100) -> int:
        events = await self._reader.due_retries(self._clock.now(), limit)
        for event in events:
            await self._runner.process(event.id)
        return len(events)
