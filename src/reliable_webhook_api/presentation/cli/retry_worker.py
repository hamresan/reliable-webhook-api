import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from reliable_webhook_api.application.processing import ProcessingFailureMapper
from reliable_webhook_api.application.use_cases import ProcessReceivedEvent
from reliable_webhook_api.config import get_settings
from reliable_webhook_api.domain import EventTransitionPolicy
from reliable_webhook_api.infrastructure.clock import SystemClock
from reliable_webhook_api.infrastructure.persistence import (
    SqlAlchemyEventRepository,
    SqlAlchemyUnitOfWork,
    create_database_engine,
    create_session_factory,
)
from reliable_webhook_api.infrastructure.processing import DeterministicEventProcessor
from reliable_webhook_api.infrastructure.processing.sample_handlers import (
    handle_customer_created,
    handle_invoice_paid,
)
from reliable_webhook_api.infrastructure.workers import RetryWorker


def build_processing_command(session: AsyncSession) -> ProcessReceivedEvent:
    return ProcessReceivedEvent(
        repository=SqlAlchemyEventRepository(session),
        processor=DeterministicEventProcessor(
            {
                "customer.created": handle_customer_created,
                "invoice.paid": handle_invoice_paid,
            }
        ),
        clock=SystemClock(),
        unit_of_work=SqlAlchemyUnitOfWork(session),
        transition_policy=EventTransitionPolicy(),
        failure_mapper=ProcessingFailureMapper(),
    )


async def run() -> int:
    engine = create_database_engine(get_settings().database_url)
    try:
        worker = RetryWorker(
            session_factory=create_session_factory(engine),
            command_factory=build_processing_command,
            clock=SystemClock(),
        )
        return await worker.run_once()
    finally:
        await engine.dispose()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
