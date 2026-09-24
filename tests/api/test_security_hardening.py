import json
from uuid import uuid4

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from reliable_webhook_api.presentation.api.app import create_app


async def test_oversized_payload_is_rejected_before_processing() -> None:
    app = create_app()
    body = b"x" * 1_048_577

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post("/webhooks/events", content=body)

    assert response.status_code == 413
    assert response.json() == {"detail": "Request payload is too large."}


async def test_invalid_signature_response_does_not_echo_signature_or_payload() -> None:
    app = create_app()
    body = json.dumps(
        {
            "event_id": str(uuid4()),
            "event_type": "invoice.paid",
            "occurred_at": "2026-09-24T12:00:00Z",
            "data": {"secret_value": "must-not-echo"},
        }
    ).encode()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/webhooks/events",
            content=body,
            headers={"X-Webhook-Signature": "not-valid"},
        )

    assert response.status_code == 401
    assert "not-valid" not in response.text
    assert "must-not-echo" not in response.text


async def test_unhandled_errors_do_not_include_debug_trace() -> None:
    app = FastAPI(debug=False)

    @app.get("/boom")
    async def boom() -> None:
        raise RuntimeError("sensitive internal detail")

    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
        response = await client.get("/boom")

    assert response.status_code == 500
    assert "Traceback" not in response.text
    assert "sensitive internal detail" not in response.text
