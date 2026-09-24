from collections.abc import AsyncIterator
from datetime import timedelta
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from reliable_webhook_api.application.operations import OperationalEventMapper
from reliable_webhook_api.application.use_cases import GetEvent, ListEvents, RetryEvent
from reliable_webhook_api.config import get_settings
from reliable_webhook_api.domain import (
    EventTransitionPolicy,
    ExponentialBackoff,
    MaxAttempts,
    RetryPolicy,
    RetryableFailurePolicy,
)
from reliable_webhook_api.infrastructure.clock import SystemClock
from reliable_webhook_api.infrastructure.persistence import (
    SqlAlchemyEventQuery,
    SqlAlchemyEventRepository,
    SqlAlchemyUnitOfWork,
)
from reliable_webhook_api.infrastructure.scheduling import SqlAlchemyRetryScheduler
from reliable_webhook_api.presentation.api.dependencies.webhooks import get_session_factory


async def get_session() -> AsyncIterator[AsyncSession]:
    async with get_session_factory()() as session:
        yield session


SessionDependency = Annotated[AsyncSession, Depends(get_session)]


def get_event_use_case(session: SessionDependency) -> GetEvent:
    return GetEvent(SqlAlchemyEventQuery(session), OperationalEventMapper())


def get_list_events_use_case(session: SessionDependency) -> ListEvents:
    return ListEvents(SqlAlchemyEventQuery(session), OperationalEventMapper())


def get_retry_event_use_case(session: SessionDependency) -> RetryEvent:
    settings = get_settings()
    return RetryEvent(
        repository=SqlAlchemyEventRepository(session),
        scheduler=SqlAlchemyRetryScheduler(session),
        clock=SystemClock(),
        unit_of_work=SqlAlchemyUnitOfWork(session),
        retry_policy=RetryPolicy(MaxAttempts(settings.retry_max_attempts)),
        retryable_failures=RetryableFailurePolicy(frozenset({"processor_error"})),
        backoff=ExponentialBackoff(
            base_delay=timedelta(seconds=settings.retry_base_delay_seconds),
            max_delay=timedelta(seconds=settings.retry_max_delay_seconds),
        ),
        transition_policy=EventTransitionPolicy(),
    )
