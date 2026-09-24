from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from reliable_webhook_api.application.errors import DuplicateEventError
from reliable_webhook_api.application.ports import EventRepository
from reliable_webhook_api.domain import EventId, EventStatus, WebhookEvent
from reliable_webhook_api.infrastructure.persistence.event_mapper import EventPersistenceMapper
from reliable_webhook_api.infrastructure.persistence.models import EventModel


class SqlAlchemyEventRepository(EventRepository):
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

    async def add(self, event: WebhookEvent) -> None:
        model = EventPersistenceMapper.to_model(event, datetime.now(UTC))
        self._session.add(model)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            await self._session.rollback()
            raise DuplicateEventError("Webhook event already exists.") from exc

    async def save(self, event: WebhookEvent) -> None:
        statement = (
            select(EventModel)
            .where(EventModel.event_id == event.id.value)
            .options(selectinload(EventModel.attempts))
        )
        model = await self._session.scalar(statement)
        if model is None:
            await self.add(event)
            return

        model.event_type = event.event_type.value
        model.payload = event.data
        model.occurred_at = event.occurred_at.value
        model.received_at = event.received_at.value
        model.status = event.status.value
        model.failure_code = event.failure_reason.code.value if event.failure_reason else None
        model.failure_message = event.failure_reason.message.value if event.failure_reason else None
        model.version += 1
        model.updated_at = datetime.now(UTC)
        model.attempts = [
            EventPersistenceMapper.attempt_to_model(attempt) for attempt in event.attempts
        ]
        await self._session.flush()

    async def list(self, status: EventStatus | None = None) -> list[WebhookEvent]:
        statement = select(EventModel).options(selectinload(EventModel.attempts))
        if status is not None:
            statement = statement.where(EventModel.status == status.value)
        statement = statement.order_by(EventModel.received_at, EventModel.event_id)
        models = (await self._session.scalars(statement)).all()
        return [EventPersistenceMapper.to_domain(model) for model in models]
