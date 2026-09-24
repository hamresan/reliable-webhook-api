from sqlalchemy.ext.asyncio import AsyncSession

from reliable_webhook_api.application.use_cases import ProcessReceivedEvent
from reliable_webhook_api.config import Settings
from reliable_webhook_api.infrastructure.scheduling import InProcessRetryScheduler
from reliable_webhook_api.presentation.cli.retry_worker import build_processing_command


async def test_build_processing_command_composes_stage_five_dependencies() -> None:
    async with AsyncSession() as session:
        command = build_processing_command(
            session=session,
            settings=Settings(),
            scheduler=InProcessRetryScheduler(),
        )

    assert isinstance(command, ProcessReceivedEvent)
