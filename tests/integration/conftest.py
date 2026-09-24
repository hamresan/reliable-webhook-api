import os
from collections.abc import AsyncIterator, Iterator

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from reliable_webhook_api.config import get_settings
from reliable_webhook_api.infrastructure.persistence import (
    create_database_engine,
    create_session_factory,
)
from reliable_webhook_api.infrastructure.persistence.models import (
    EventModel,
    ProcessingAttemptModel,
)

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    if TEST_DATABASE_URL is not None:
        return

    skip_postgres = pytest.mark.skip(
        reason="PostgreSQL integration tests require TEST_DATABASE_URL.",
    )
    for item in items:
        if item.nodeid.startswith("tests/integration/"):
            item.add_marker(skip_postgres)


@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> Iterator[None]:
    if TEST_DATABASE_URL is None:
        yield
        return

    os.environ["APP_DATABASE_URL"] = TEST_DATABASE_URL
    get_settings.cache_clear()
    config = Config("alembic.ini")
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    yield
    command.downgrade(config, "base")
    get_settings.cache_clear()


@pytest.fixture(scope="session")
async def database_engine() -> AsyncIterator[AsyncEngine]:
    if TEST_DATABASE_URL is None:
        pytest.skip("PostgreSQL integration tests require TEST_DATABASE_URL.")

    engine = create_database_engine(TEST_DATABASE_URL)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session_factory(
    database_engine: AsyncEngine,
) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    factory = create_session_factory(database_engine)
    async with factory() as session:
        await session.execute(delete(ProcessingAttemptModel))
        await session.execute(delete(EventModel))
        await session.commit()
    yield factory
