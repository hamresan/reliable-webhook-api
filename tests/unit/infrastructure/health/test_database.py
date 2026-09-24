from unittest.mock import AsyncMock, MagicMock

from reliable_webhook_api.infrastructure.health import DatabaseReadinessChecker


async def test_readiness_returns_true_when_database_connects() -> None:
    connection = AsyncMock()
    context = AsyncMock()
    context.__aenter__.return_value = connection
    engine = MagicMock()
    engine.connect.return_value = context

    checker = DatabaseReadinessChecker(engine)

    assert await checker.is_ready() is True
    connection.execute.assert_awaited_once()


async def test_readiness_returns_false_when_database_connection_fails() -> None:
    context = AsyncMock()
    context.__aenter__.side_effect = RuntimeError("db down")
    engine = MagicMock()
    engine.connect.return_value = context

    checker = DatabaseReadinessChecker(engine)

    assert await checker.is_ready() is False
