from datetime import datetime

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from reliable_webhook_api.application.ports import RetryScheduler
from reliable_webhook_api.domain import EventId
from reliable_webhook_api.infrastructure.persistence.models import EventModel


class SqlAlchemyRetryScheduler(RetryScheduler):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def schedule(self, event_id: EventId, due_at: datetime) -> None:
        await self._session.execute(
            update(EventModel)
            .where(EventModel.event_id == event_id.value)
            .values(next_retry_at=due_at)
        )
