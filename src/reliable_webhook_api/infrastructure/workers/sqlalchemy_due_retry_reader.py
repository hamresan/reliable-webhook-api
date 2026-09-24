from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from reliable_webhook_api.application.ports import DueRetryReader
from reliable_webhook_api.domain import WebhookEvent
from reliable_webhook_api.infrastructure.persistence import SqlAlchemyEventQuery


class SqlAlchemyDueRetryReader(DueRetryReader):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def due_retries(self, due_at: datetime, limit: int) -> list[WebhookEvent]:
        async with self._session_factory() as session:
            return await SqlAlchemyEventQuery(session).due_retries(due_at, limit)
