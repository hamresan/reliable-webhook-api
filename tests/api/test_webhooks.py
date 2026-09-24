from uuid import UUID

from httpx import ASGITransport, AsyncClient
from tests.api.support import build_receive_use_case, sign

from reliable_webhook_api.config import get_settings
from reliable_webhook_api.infrastructure.persistence import InMemoryEventRepository
from reliable_webhook_api.presentation.api.app import create_app
from reliable_webhook_api.presentation.api.dependencies import get_receive_webhook_event

SECRET = "stage-two-test-secret"
EVENT_ID = UUID("00000000-0000-0000-0000-000000000001")


async def post_raw(payload: bytes, signature: str | None):
    app = create_app()
    repository = InMemoryEventRepository()
    app.dependency_overrides[get_receive_webhook_event] = lambda: build_receive_use_case(
        repository,
        SECRET,
    )
    settings = get_settings()

    headers = {"content-type": "application/json"}
    if signature is not None:
        headers[settings.webhook_signature_header] = signature

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post("/webhooks/events", content=payload, headers=headers)

    return response, repository


async def test_accepts_signature_for_exact_http_bytes() -> None:
    payload = (
        b'{"event_id":"00000000-0000-0000-0000-000000000001",'
        b'"event_type":"invoice.paid","occurred_at":"2026-09-24T12:00:00Z",'
        b'"data":{"amount":100}}'
    )

    response, repository = await post_raw(payload, sign(SECRET, payload))

    assert response.status_code == 202
    assert response.json() == {
        "event_id": str(EVENT_ID),
        "status": "received",
        "duplicate": False,
    }
    assert repository.count() == 1


async def test_reserialized_json_signature_does_not_verify_different_http_bytes() -> None:
    compact = (
        b'{"event_id":"00000000-0000-0000-0000-000000000001",'
        b'"event_type":"invoice.paid","occurred_at":"2026-09-24T12:00:00Z",'
        b'"data":{"amount":100}}'
    )
    spaced = (
        b'{ "event_id": "00000000-0000-0000-0000-000000000001", '
        b'"event_type": "invoice.paid", "occurred_at": "2026-09-24T12:00:00Z", '
        b'"data": {"amount": 100} }'
    )

    response, repository = await post_raw(spaced, sign(SECRET, compact))

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid webhook signature."}
    assert repository.is_empty()


async def test_duplicate_delivery_returns_success_without_second_event() -> None:
    payload = (
        b'{"event_id":"00000000-0000-0000-0000-000000000001",'
        b'"event_type":"invoice.paid","occurred_at":"2026-09-24T12:00:00Z",'
        b'"data":{"amount":100}}'
    )
    app = create_app()
    repository = InMemoryEventRepository()
    app.dependency_overrides[get_receive_webhook_event] = lambda: build_receive_use_case(
        repository,
        SECRET,
    )

    headers = {
        "content-type": "application/json",
        get_settings().webhook_signature_header: sign(SECRET, payload),
    }
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        first = await client.post("/webhooks/events", content=payload, headers=headers)
        second = await client.post("/webhooks/events", content=payload, headers=headers)

    assert first.status_code == 202
    assert second.status_code == 200
    assert second.json()["duplicate"] is True
    assert repository.count() == 1


async def test_missing_or_invalid_signature_is_safe_and_not_persisted() -> None:
    payload = (
        b'{"event_id":"00000000-0000-0000-0000-000000000001",'
        b'"event_type":"invoice.paid","occurred_at":"2026-09-24T12:00:00Z","data":{}}'
    )

    missing, missing_repository = await post_raw(payload, None)
    invalid, invalid_repository = await post_raw(payload, "0" * 64)

    assert missing.status_code == 401
    assert invalid.status_code == 401
    assert missing.json() == {"detail": "Invalid webhook signature."}
    assert invalid.json() == {"detail": "Invalid webhook signature."}
    assert missing_repository.is_empty()
    assert invalid_repository.is_empty()


async def test_invalid_envelope_returns_bad_request_after_valid_signature() -> None:
    payload = b'{"event_id":"not-a-uuid","event_type":"","occurred_at":"bad","data":{}}'

    response, repository = await post_raw(payload, sign(SECRET, payload))

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid webhook event envelope."}
    assert repository.is_empty()
