from reliable_webhook_api.application.errors import InvalidTransitionError
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
        processed = 0
        for event in events:
            try:
                await self._runner.process(event.id)
            except InvalidTransitionError:
                continue
            processed += 1
        return processed
