from tests.unit.application.support import build_event
from tests.unit.application.support.event_builder import NOW

from reliable_webhook_api.infrastructure.scheduling import InProcessRetryScheduler


async def test_scheduler_records_requested_retry_without_persistence() -> None:
    event = build_event()
    scheduler = InProcessRetryScheduler()

    await scheduler.schedule(event.id, NOW)

    assert scheduler.scheduled == ((event.id, NOW),)
