from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from reliable_webhook_api.application.dto import ProcessEventOutput
from reliable_webhook_api.application.ports import EventProcessingCommand
from reliable_webhook_api.domain import (
    EventId,
    EventStatus,
    EventType,
    OccurredAt,
    ReceivedAt,
    WebhookEvent,
)
from reliable_webhook_api.infrastructure.persistence import (
    SqlAlchemyEventRepository,
    SqlAlchemyUnitOfWork,
)
from reliable_webhook_api.infrastructure.workers import RetryWorker
from tests.unit.application.use_cases.fakes import FakeClock

NOW = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)


class RecordingCommand(EventProcessingCommand):
    def __init__(self) -> None:
        self.event_ids: list[EventId] = []

    async def execute(self, event_id: EventId) -> ProcessEventOutput:
        self.event_ids.append(event_id)
        return ProcessEventOutput(event_id=event_id.value, status=EventStatus.PROCESSED)


async def test_worker_processes_due_events_with_fresh_sessions(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    event = WebhookEvent(
        id=EventId(UUID("00000000-0000-0000-0000-000000000508")),
        event_type=EventType("invoice.paid"),
        occurred_at=OccurredAt(NOW),
        data={},
        status=EventStatus.RETRY_SCHEDULED,
        received_at=ReceivedAt(NOW),
        next_retry_at=NOW,
    )
    async with session_factory() as session:
        async with SqlAlchemyUnitOfWork(session):
            await SqlAlchemyEventRepository(session).add(event)

    command = RecordingCommand()

    def command_factory(session: AsyncSession) -> EventProcessingCommand:
        del session
        return command

    count = await RetryWorker(
        session_factory=session_factory,
        command_factory=command_factory,
        clock=FakeClock(NOW),
    ).run_once()

    assert count == 1
    assert command.event_ids == [event.id]
