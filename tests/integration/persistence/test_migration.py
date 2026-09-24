from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncEngine


async def test_migration_creates_required_tables(database_engine: AsyncEngine) -> None:
    async with database_engine.connect() as connection:
        tables = await connection.run_sync(
            lambda sync_connection: inspect(sync_connection).get_table_names()
        )

    assert "webhook_events" in tables
    assert "processing_attempts" in tables

    async with database_engine.connect() as connection:
        columns = await connection.run_sync(
            lambda sync_connection: {
                column["name"] for column in inspect(sync_connection).get_columns("webhook_events")
            }
        )

    assert "next_retry_at" in columns
