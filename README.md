# Reliable Webhook API

> A provider-neutral FastAPI service for receiving signed webhook events safely, deduplicating deliveries, persisting event state, and handling bounded retries.

**Status:** Under active development. The repository currently contains the public project contract and implementation roadmap. The installation and API examples below describe the planned **v0.1.0** interface; run them after the corresponding implementation stages have been completed.

## Why this project exists

Webhook delivery is usually **at least once**: the sending service may resend the same event after a timeout or network failure. A reliable receiver must therefore verify that requests are authentic, store the event safely, avoid repeated side effects, and make failures visible and recoverable.

This project demonstrates a focused backend workflow often needed for Stripe, Shopify, Meta, and SaaS integrations:

- HMAC-SHA256 signature verification using raw request bytes
- Idempotent receipt based on an external `event_id`
- Persisted event lifecycle: `received`, `processing`, `processed`, and `failed`
- Bounded, policy-controlled retries for safe failures
- Query endpoints for operational visibility
- Clear API contracts, OpenAPI/Swagger documentation, Docker support, and automated tests

It intentionally starts with a generic webhook envelope instead of claiming compatibility with every provider. Provider adapters can be added later without changing the core business rules.

## What this demonstrates

A portfolio project should show more than an endpoint that accepts JSON. This repository is designed to demonstrate practical backend skills relevant to client work:

| Area | Demonstrated approach |
| --- | --- |
| API design | FastAPI endpoints, validation, accurate HTTP errors, and OpenAPI |
| Security | HMAC verification, constant-time comparison, secret-safe logs |
| Reliability | Idempotency, durable event state, processing attempts, bounded retries |
| Data | PostgreSQL persistence, migrations, repository pattern, transaction boundaries |
| Architecture | Clean Architecture, explicit ports/adapters, dependency inversion |
| Delivery | Docker Compose, CI checks, Ruff, Pyright, pytest, and meaningful coverage |

## Planned architecture

```text
HTTP request
    │
    ▼
FastAPI adapter ──► signature verifier ──► ReceiveWebhookEvent use case
                                                  │
                                                  ▼
                                           Event repository
                                                  │
                                                  ▼
                                        Worker / processor port
                                                  │
                                                  ▼
                                processed | failed | retry scheduled
```

The domain and application layers do not depend on FastAPI, SQLAlchemy, or a webhook vendor SDK. Infrastructure adapters implement the database, HMAC verification, configuration, clock, and event processing ports.

## Event lifecycle

```text
received → processing → processed
                 │
                 └→ failed → retry_scheduled → processing
```

A duplicate delivery with the same `event_id` is acknowledged with a stable successful result and is **not processed a second time**.

> Idempotency prevents duplicate work inside this service. It cannot by itself guarantee exactly-once effects in external systems; integrations must use their own idempotency controls where required.

## Technology stack

- Python 3.12
- FastAPI and Uvicorn
- SQLAlchemy (async) and Alembic
- PostgreSQL for runtime; SQLite for focused tests where compatible
- `uv` for dependency and environment management
- Docker and Docker Compose
- pytest, HTTPX, Ruff, and Pyright

## Prerequisites

For the planned v0.1.0 release:

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Docker Desktop / Docker Engine with Docker Compose (recommended for PostgreSQL)

## Installation

### Option A — Docker Compose (recommended)

```bash
git clone https://github.com/hamresan/reliable-webhook-api.git
cd reliable-webhook-api

cp .env.example .env
# Set WEBHOOK_SIGNING_SECRET to a local development value.

docker compose up --build
```

The API will be available at:

- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`

### Option B — Local development

```bash
git clone https://github.com/hamresan/reliable-webhook-api.git
cd reliable-webhook-api

cp .env.example .env
uv sync
uv run alembic upgrade head
uv run uvicorn reliable_webhook_api.presentation.api:app --reload
```

Run a PostgreSQL database locally and set `DATABASE_URL` in `.env` before applying migrations.

## Configuration

The planned environment contract is:

```dotenv
# Required outside tests. Never commit a real value.
WEBHOOK_SIGNING_SECRET=change-me-for-local-development

# PostgreSQL runtime URL example
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/webhooks

# Operational settings
MAX_PROCESSING_ATTEMPTS=3
MAX_REQUEST_BODY_BYTES=1048576
LOG_LEVEL=INFO
```

Use a secret manager and TLS termination appropriate to the deployment environment. Do not place real signing secrets in source code, README examples, issues, or commits.

## Quick start: send a signed event

After the API is implemented and running, create a JSON payload:

```json
{
  "event_id": "evt_01JQ8S74VQ5YB6A5T2M0KX4E9F",
  "event_type": "customer.created",
  "occurred_at": "2026-09-24T10:30:00Z",
  "data": {
    "customer_id": "cus_123",
    "email": "customer@example.com"
  }
}
```

The signature must be computed from the **exact raw bytes** transmitted in the HTTP body.

```bash
payload='{"event_id":"evt_01JQ8S74VQ5YB6A5T2M0KX4E9F","event_type":"customer.created","occurred_at":"2026-09-24T10:30:00Z","data":{"customer_id":"cus_123","email":"customer@example.com"}}'

signature=$(printf '%s' "$payload" \
  | openssl dgst -sha256 -hmac "$WEBHOOK_SIGNING_SECRET" -hex \
  | sed 's/^.* //')

curl --request POST "http://localhost:8000/webhooks/events" \
  --header "Content-Type: application/json" \
  --header "X-Webhook-Signature: sha256=$signature" \
  --data "$payload"
```

Expected v0.1.0 response:

```json
{
  "event_id": "evt_01JQ8S74VQ5YB6A5T2M0KX4E9F",
  "status": "received",
  "duplicate": false
}
```

Send the identical payload again to demonstrate idempotency:

```json
{
  "event_id": "evt_01JQ8S74VQ5YB6A5T2M0KX4E9F",
  "status": "received",
  "duplicate": true
}
```

## Planned API contract

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/webhooks/events` | Verify and receive a signed event |
| `GET` | `/events/{event_id}` | Inspect one event and its processing state |
| `GET` | `/events?status=failed&limit=20` | List operational events with pagination |
| `POST` | `/events/{event_id}/retry` | Request a policy-approved manual retry |
| `GET` | `/health` | Liveness/readiness checks |

Invalid or missing signatures are rejected before payload persistence and before any processor is invoked. Failure responses do not echo signatures, secrets, or raw payloads.

## Development and testing

Once the project foundation is implemented, run the complete quality gate:

```bash
uv run ruff check src tests
uv run ruff format --check src tests
uv run pyright src tests
uv run pytest --cov=src --cov-report=term-missing
```

The project uses real, mirrored tests:

- **Unit tests** cover domain state transitions, policies, HMAC verification, and use cases using fakes.
- **Integration tests** exercise real repository and migration behaviour, including database-enforced duplicate event IDs.
- **API tests** send signed raw bodies through the ASGI app and verify HTTP contracts.
- **Smoke tests** validate the Docker Compose workflow when it is added.

The target is at least **90% total coverage** after the core receipt stage and **95%+** in domain/application layers, with behaviour-focused assertions rather than coverage-only tests.

## Roadmap

Implementation is broken into independently reviewed stages. Each stage has its own branch and may be merged only after linting, formatting, type checks, tests, coverage, and CI pass.

1. Project foundation and developer experience
2. Domain model, event state machine, and application ports
3. Signature verification, receipt endpoint, and idempotency
4. PostgreSQL persistence, migrations, and transactional duplicate handling
5. Processing orchestration and failure recording
6. Retry policy, worker/CLI, and operational endpoints
7. Docker, configuration, observability, and security hardening
8. Documentation, examples, and v0.1.0 release

See [the implementation roadmap](./02-%20reliable_webhook_api_implementation_roadmap.md) for acceptance criteria, test requirements, and merge gates. The roadmap file will be added to the repository alongside the first implementation stage.

## Security notes

- Verify the signature against raw bytes, not a re-serialized JSON object.
- Use a constant-time signature comparison.
- Treat every delivery as untrusted until verification succeeds.
- Enforce a request-body size limit and configure rate limiting at the deployment edge.
- Persist only the event data your use case needs; define retention requirements before production use.
- Restrict operational event endpoints with authentication/authorization in a real deployment.
- Use HTTPS in every environment that receives external webhooks.

## Scope and limitations

Version `0.1.0` is a focused reference implementation. It does not yet claim:

- Drop-in compatibility with Stripe, Shopify, Meta, or every provider protocol
- Distributed queues, multi-region delivery, or external exactly-once guarantees
- A complete operational dashboard
- Production authentication for the operational endpoints

Those are valuable extensions, but keeping the initial scope small makes the reliability guarantees understandable and testable.

## Contributing

Contributions and feedback are welcome after the initial implementation is available. Please keep changes focused, add tests that mirror the affected layer, run the quality checks above, and avoid committing secrets or generated database files.

## License

This project will be released under the [MIT License](./LICENSE).
