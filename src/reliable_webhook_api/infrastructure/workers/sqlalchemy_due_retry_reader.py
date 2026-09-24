from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from reliable_webhook_api.application.ports import DueRetryReader
from reliable_webhook_api.domain import EventStatus, WebhookEvent
from reliable_webhook_api.infrastructure.persistence.event_mapper import EventPersistenceMapper
from reliable_webhook_api.infrastructure.persistence.models import EventModel


class SqlAlchemyDueRetryReader(DueRetryReader):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def due_retries(self, due_at: datetime, limit: int) -> list[WebhookEvent]:
        statement = (
            select(EventModel)
            .where(
                EventModel.status == EventStatus.RETRY_SCHEDULED.value,
                EventModel.next_retry_at.is_not(None),
                EventModel.next_retry_at <= due_at,
            )
            .options(selectinload(EventModel.attempts))
            .order_by(EventModel.next_retry_at, EventModel.event_id)
            .limit(limit)
        )
        async with self._session_factory() as session:
            models = (await session.scalars(statement)).all()
        return [EventPersistenceMapper.to_domain(model) for model in models]
