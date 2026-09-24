import asyncio
from functools import partial

from sqlalchemy.ext.asyncio import AsyncSession

from reliable_webhook_api.application.processing import ProcessingFailureMapper
from reliable_webhook_api.application.retries import RetryCoordinator
from reliable_webhook_api.application.use_cases import ProcessDueRetries, ProcessReceivedEvent
from reliable_webhook_api.config import Settings, get_settings
from reliable_webhook_api.domain import (
    EventTransitionPolicy,
    ExponentialBackoff,
    MaxAttempts,
    RetryableFailurePolicy,
    RetryPolicy,
)
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
from reliable_webhook_api.infrastructure.scheduling import InProcessRetryScheduler
from reliable_webhook_api.infrastructure.workers import (
    RetryWorker,
    SessionProcessingRunner,
    SqlAlchemyDueRetryReader,
)


def build_processing_command(
    session: AsyncSession,
    settings: Settings,
    scheduler: InProcessRetryScheduler,
) -> ProcessReceivedEvent:
    repository = SqlAlchemyEventRepository(session)
    clock = SystemClock()
    retry_coordinator = RetryCoordinator(
        repository=repository,
        scheduler=scheduler,
        clock=clock,
        retry_policy=RetryPolicy(MaxAttempts(settings.retry_max_attempts)),
        retryable_failures=RetryableFailurePolicy(frozenset({"processor_error"})),
        backoff=ExponentialBackoff(
            base_delay=settings.retry_base_delay,
            max_delay=settings.retry_max_delay,
        ),
        transition_policy=EventTransitionPolicy(),
    )
    return ProcessReceivedEvent(
        repository=repository,
        processor=DeterministicEventProcessor(
            {
                "customer.created": handle_customer_created,
                "invoice.paid": handle_invoice_paid,
            }
        ),
        clock=clock,
        unit_of_work=SqlAlchemyUnitOfWork(session),
        transition_policy=EventTransitionPolicy(),
        failure_mapper=ProcessingFailureMapper(),
        retry_coordinator=retry_coordinator,
    )


async def run() -> int:
    settings = get_settings()
    engine = create_database_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    scheduler = InProcessRetryScheduler()
    command_factory = partial(
        build_processing_command,
        settings=settings,
        scheduler=scheduler,
    )
    try:
        use_case = ProcessDueRetries(
            reader=SqlAlchemyDueRetryReader(session_factory),
            runner=SessionProcessingRunner(session_factory, command_factory),
            clock=SystemClock(),
        )
        return await RetryWorker(use_case).run_once()
    finally:
        await engine.dispose()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
