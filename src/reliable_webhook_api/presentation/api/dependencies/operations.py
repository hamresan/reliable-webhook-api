from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from reliable_webhook_api.application.operations import OperationalEventMapper
from reliable_webhook_api.application.retries import RetryCoordinator
from reliable_webhook_api.application.use_cases import GetEvent, ListEvents, RetryEvent
from reliable_webhook_api.config import get_settings
from reliable_webhook_api.domain import (
    EventTransitionPolicy,
    ExponentialBackoff,
    MaxAttempts,
    RetryableFailurePolicy,
    RetryPolicy,
)
from reliable_webhook_api.infrastructure.clock import SystemClock
from reliable_webhook_api.infrastructure.persistence import (
    SqlAlchemyEventQuery,
    SqlAlchemyEventRepository,
    SqlAlchemyUnitOfWork,
)
from reliable_webhook_api.infrastructure.scheduling import InProcessRetryScheduler
from reliable_webhook_api.presentation.api.dependencies.webhooks import get_session_factory


async def get_session() -> AsyncIterator[AsyncSession]:
    async with get_session_factory()() as session:
        yield session


SessionDependency = Annotated[AsyncSession, Depends(get_session)]


@lru_cache
def get_retry_scheduler() -> InProcessRetryScheduler:
    return InProcessRetryScheduler()


def build_retry_coordinator(
    repository: SqlAlchemyEventRepository,
) -> RetryCoordinator:
    settings = get_settings()
    return RetryCoordinator(
        repository=repository,
        scheduler=get_retry_scheduler(),
        clock=SystemClock(),
        retry_policy=RetryPolicy(MaxAttempts(settings.retry_max_attempts)),
        retryable_failures=RetryableFailurePolicy(frozenset({"processor_error"})),
        backoff=ExponentialBackoff(
            base_delay=settings.retry_base_delay,
            max_delay=settings.retry_max_delay,
        ),
        transition_policy=EventTransitionPolicy(),
    )


def get_event_use_case(session: SessionDependency) -> GetEvent:
    return GetEvent(SqlAlchemyEventQuery(session), OperationalEventMapper())


def get_list_events_use_case(session: SessionDependency) -> ListEvents:
    return ListEvents(SqlAlchemyEventQuery(session), OperationalEventMapper())


def get_retry_event_use_case(session: SessionDependency) -> RetryEvent:
    repository = SqlAlchemyEventRepository(session)
    return RetryEvent(
        repository=repository,
        unit_of_work=SqlAlchemyUnitOfWork(session),
        retry_coordinator=build_retry_coordinator(repository),
    )
