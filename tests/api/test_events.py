from httpx import ASGITransport, AsyncClient

from reliable_webhook_api.application.errors import NotFoundError
from reliable_webhook_api.presentation.api.app import create_app
from reliable_webhook_api.presentation.api.dependencies.operations import (
    get_event_use_case,
    get_list_events_use_case,
    get_retry_event_use_case,
)
from tests.api.operations_support import (
    EVENT_ID,
    StubGetEvent,
    StubListEvents,
    StubRetryEvent,
    terminal_retry_error,
)


async def request(
    method: str,
    path: str,
    *,
    get_event: StubGetEvent | None = None,
    list_events: StubListEvents | None = None,
    retry_event: StubRetryEvent | None = None,
):
    app = create_app()
    if get_event is not None:
        app.dependency_overrides[get_event_use_case] = lambda: get_event
    if list_events is not None:
        app.dependency_overrides[get_list_events_use_case] = lambda: list_events
    if retry_event is not None:
        app.dependency_overrides[get_retry_event_use_case] = lambda: retry_event

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.request(method, path)


async def test_get_event_returns_operational_state_without_payload() -> None:
    response = await request("GET", f"/events/{EVENT_ID}", get_event=StubGetEvent())

    assert response.status_code == 200
    body = response.json()
    assert body["event_id"] == str(EVENT_ID)
    assert body["status"] == "failed"
    assert "data" not in body


async def test_get_event_maps_not_found() -> None:
    response = await request("GET", f"/events/{EVENT_ID}", get_event=StubGetEvent(missing=True))

    assert response.status_code == 404


async def test_list_events_accepts_filter_and_pagination() -> None:
    response = await request(
        "GET",
        "/events?status=failed&offset=10&limit=20",
        list_events=StubListEvents(),
    )

    assert response.status_code == 200
    assert response.json()["offset"] == 10
    assert response.json()["limit"] == 20
    assert response.json()["total"] == 1


async def test_list_events_rejects_invalid_pagination() -> None:
    response = await request("GET", "/events?limit=0", list_events=StubListEvents())

    assert response.status_code == 422


async def test_retry_returns_accepted_schedule() -> None:
    response = await request(
        "POST",
        f"/events/{EVENT_ID}/retry",
        retry_event=StubRetryEvent(),
    )

    assert response.status_code == 202
    assert response.json()["status"] == "retry_scheduled"


async def test_retry_maps_not_found_and_terminal_conflict() -> None:
    missing = await request(
        "POST",
        f"/events/{EVENT_ID}/retry",
        retry_event=StubRetryEvent(NotFoundError("missing")),
    )
    terminal = await request(
        "POST",
        f"/events/{EVENT_ID}/retry",
        retry_event=StubRetryEvent(terminal_retry_error()),
    )

    assert missing.status_code == 404
    assert terminal.status_code == 409
