from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from reliable_webhook_api.application.ports import Clock, EventProcessingCommand
from reliable_webhook_api.infrastructure.persistence import SqlAlchemyEventQuery

ProcessingCommandFactory = Callable[[AsyncSession], EventProcessingCommand]


class RetryWorker:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        command_factory: ProcessingCommandFactory,
        clock: Clock,
    ) -> None:
        self._session_factory = session_factory
        self._command_factory = command_factory
        self._clock = clock

    async def run_once(self, limit: int = 100) -> int:
        async with self._session_factory() as session:
            due_events = await SqlAlchemyEventQuery(session).due_retries(self._clock.now(), limit)
            event_ids = [event.id for event in due_events]

        for event_id in event_ids:
            async with self._session_factory() as session:
                await self._command_factory(session).execute(event_id)

        return len(event_ids)
