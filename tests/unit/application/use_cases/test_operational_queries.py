import pytest

from reliable_webhook_api.application.errors import NotFoundError
from reliable_webhook_api.application.operations import OperationalEventMapper
from reliable_webhook_api.application.use_cases import GetEvent, ListEvents
from reliable_webhook_api.domain import EventId, EventStatus
from tests.unit.application.support import FakeEventQuery, build_event


async def test_get_event_returns_sanitized_operational_dto() -> None:
    event = build_event()
    result = await GetEvent(
        FakeEventQuery([event]),
        OperationalEventMapper(),
    ).execute(event.id)

    assert result.event_id == event.id.value
    assert result.failure_code == "processor_error"
    assert result.attempts[0].failure_code == "processor_error"
    assert not hasattr(result, "data")


async def test_get_event_raises_not_found() -> None:
    event_id = build_event().id
    with pytest.raises(NotFoundError):
        await GetEvent(FakeEventQuery([]), OperationalEventMapper()).execute(event_id)


async def test_list_events_preserves_filter_and_pagination_metadata() -> None:
    failed = build_event()
    processed = build_event(status=EventStatus.PROCESSED)

    result = await ListEvents(
        FakeEventQuery([failed, processed]),
        OperationalEventMapper(),
    ).execute(EventStatus.FAILED, 0, 1)

    assert result.total == 1
    assert result.offset == 0
    assert result.limit == 1
    assert [item.status for item in result.items] == [EventStatus.FAILED]
