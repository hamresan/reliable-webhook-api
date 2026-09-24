from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from reliable_webhook_api.application.ports import EventPage, EventQuery
from reliable_webhook_api.domain import EventId, EventStatus, WebhookEvent
from reliable_webhook_api.infrastructure.persistence.event_mapper import EventPersistenceMapper
from reliable_webhook_api.infrastructure.persistence.models import EventModel


class SqlAlchemyEventQuery(EventQuery):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, event_id: EventId) -> WebhookEvent | None:
        statement = (
            select(EventModel)
            .where(EventModel.event_id == event_id.value)
            .options(selectinload(EventModel.attempts))
        )
        model = await self._session.scalar(statement)
        return EventPersistenceMapper.to_domain(model) if model is not None else None

    async def page(self, status: EventStatus | None, offset: int, limit: int) -> EventPage:
        filters = () if status is None else (EventModel.status == status.value,)
        count_statement = select(func.count()).select_from(EventModel).where(*filters)
        total = await self._session.scalar(count_statement)
        statement = (
            select(EventModel)
            .where(*filters)
            .options(selectinload(EventModel.attempts))
            .order_by(EventModel.received_at, EventModel.event_id)
            .offset(offset)
            .limit(limit)
        )
        models = (await self._session.scalars(statement)).all()
        return EventPage(
            items=[EventPersistenceMapper.to_domain(model) for model in models],
            total=total or 0,
        )

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
        models = (await self._session.scalars(statement)).all()
        return [EventPersistenceMapper.to_domain(model) for model in models]
