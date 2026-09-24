from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from reliable_webhook_api.application.use_cases import ReceiveWebhookEvent
from reliable_webhook_api.config import get_settings
from reliable_webhook_api.infrastructure.clock import SystemClock
from reliable_webhook_api.infrastructure.persistence import (
    SqlAlchemyEventRepository,
    SqlAlchemyUnitOfWork,
    create_database_engine,
    create_session_factory,
)
from reliable_webhook_api.infrastructure.security import HmacSha256SignatureVerifier


@lru_cache
def get_database_engine() -> AsyncEngine:
    return create_database_engine(get_settings().database_url)


@lru_cache
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return create_session_factory(get_database_engine())


async def get_receive_webhook_event() -> AsyncIterator[ReceiveWebhookEvent]:
    settings = get_settings()
    async with get_session_factory()() as session:
        repository = SqlAlchemyEventRepository(session)
        yield ReceiveWebhookEvent(
            repository=repository,
            signature_verifier=HmacSha256SignatureVerifier(settings.webhook_secret),
            clock=SystemClock(),
            unit_of_work=SqlAlchemyUnitOfWork(session),
        )
