"""Send a signed sample webhook to a running Reliable Webhook API."""

import hashlib
import hmac
import json
import os
from datetime import UTC, datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_SECRET = "replace-with-local-secret"
DEFAULT_SIGNATURE_HEADER = "X-Webhook-Signature"


def build_payload() -> bytes:
    payload = {
        "event_id": str(uuid4()),
        "event_type": "invoice.paid",
        "occurred_at": datetime.now(UTC).isoformat(),
        "data": {"invoice_id": "inv-demo"},
    }
    return json.dumps(payload, separators=(",", ":")).encode()


def sign_payload(secret: str, payload: bytes) -> str:
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def main() -> None:
    base_url = os.getenv("WEBHOOK_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    secret = os.getenv("APP_WEBHOOK_SECRET", DEFAULT_SECRET)
    signature_header = os.getenv("APP_WEBHOOK_SIGNATURE_HEADER", DEFAULT_SIGNATURE_HEADER)
    payload = build_payload()
    event_id = json.loads(payload)["event_id"]

    request = Request(
        f"{base_url}/webhooks/events",
        data=payload,
        headers={
            "Content-Type": "application/json",
            signature_header: sign_payload(secret, payload),
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=10) as response:
            print(f"POST /webhooks/events -> {response.status}")
            print(response.read().decode())

        with urlopen(f"{base_url}/events/{event_id}", timeout=10) as response:
            print(f"GET /events/{event_id} -> {response.status}")
            print(response.read().decode())
    except HTTPError as exc:
        raise SystemExit(f"HTTP {exc.code}: {exc.read().decode()}") from exc
    except URLError as exc:
        raise SystemExit(f"Unable to reach {base_url}: {exc.reason}") from exc


if __name__ == "__main__":
    main()
