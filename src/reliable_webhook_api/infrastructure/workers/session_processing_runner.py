from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from reliable_webhook_api.application.dto import ProcessEventOutput
from reliable_webhook_api.application.ports import EventProcessingCommand, EventProcessingRunner
from reliable_webhook_api.domain import EventId

ProcessingCommandFactory = Callable[[AsyncSession], EventProcessingCommand]


class SessionProcessingRunner(EventProcessingRunner):
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        command_factory: ProcessingCommandFactory,
    ) -> None:
        self._session_factory = session_factory
        self._command_factory = command_factory

    async def process(self, event_id: EventId) -> ProcessEventOutput:
        async with self._session_factory() as session:
            return await self._command_factory(session).execute(event_id)
