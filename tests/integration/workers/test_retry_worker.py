from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from reliable_webhook_api.application.ports import EventProcessingCommand
from reliable_webhook_api.application.use_cases import ProcessDueRetries
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
from reliable_webhook_api.infrastructure.workers import (
    RetryWorker,
    SessionProcessingRunner,
    SqlAlchemyDueRetryReader,
)
from tests.integration.workers.support import RecordingProcessingCommand
from tests.unit.application.use_cases.fakes import FakeClock

NOW = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)


def build_event(event_id: UUID, due_at: datetime) -> WebhookEvent:
    return WebhookEvent(
        id=EventId(event_id),
        event_type=EventType("invoice.paid"),
        occurred_at=OccurredAt(NOW),
        data={},
        status=EventStatus.RETRY_SCHEDULED,
        received_at=ReceivedAt(NOW),
        next_retry_at=due_at,
    )


async def test_worker_delegates_due_selection_and_processing_to_application(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    due = build_event(
        UUID("00000000-0000-0000-0000-000000000508"),
        NOW - timedelta(seconds=1),
    )
    future = build_event(
        UUID("00000000-0000-0000-0000-000000000509"),
        NOW + timedelta(seconds=1),
    )
    async with session_factory() as session, SqlAlchemyUnitOfWork(session):
        repository = SqlAlchemyEventRepository(session)
        await repository.add(due)
        await repository.add(future)

    command = RecordingProcessingCommand()

    def command_factory(session: AsyncSession) -> EventProcessingCommand:
        del session
        return command

    use_case = ProcessDueRetries(
        reader=SqlAlchemyDueRetryReader(session_factory),
        runner=SessionProcessingRunner(session_factory, command_factory),
        clock=FakeClock(NOW),
    )

    count = await RetryWorker(use_case).run_once()

    assert count == 1
    assert command.event_ids == [due.id]
