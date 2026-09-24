# Reliable Webhook API

> A provider-neutral FastAPI service being built stage by stage to receive signed webhook events reliably.

**Current status:** Stage 2 — signature verification and request acceptance.

The service now accepts a generic signed webhook envelope, verifies HMAC-SHA256 against the exact raw request bytes, records a newly received event through the application repository contract, and returns a stable successful response for duplicate `event_id` deliveries. Database-backed persistence and processing orchestration remain later-stage work.

## Current architecture

```text
src/reliable_webhook_api/
├── application/
│   ├── dto/
│   ├── errors/
│   ├── ports/
│   └── use_cases/
├── config/
├── domain/
├── infrastructure/
│   ├── clock/
│   ├── persistence/
│   └── security/
└── presentation/
    └── api/
        ├── dependencies/
        ├── routes/
        └── schemas/
```

Domain and application remain independent from FastAPI, SQLAlchemy, and infrastructure configuration.

## Technology stack

- Python 3.12
- FastAPI and Uvicorn
- SQLAlchemy async support and Alembic installed for upcoming persistence work
- uv
- Docker / Docker Compose
- pytest and HTTPX
- Ruff
- Pyright

## Local development

```bash
git clone https://github.com/hamresan/reliable-webhook-api.git
cd reliable-webhook-api
git checkout stage/02-event-receipt-and-idempotency

uv sync
uv run uvicorn reliable_webhook_api.presentation.api.app:app --reload
```

The API is available at `http://localhost:8000`.

### Health check

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## Webhook receipt

Configure a local secret:

```dotenv
APP_WEBHOOK_SECRET=replace-with-local-secret
APP_WEBHOOK_SIGNATURE_HEADER=X-Webhook-Signature
```

The signature is the lowercase hexadecimal HMAC-SHA256 digest of the **exact HTTP request body bytes** using `APP_WEBHOOK_SECRET`.

Generic request envelope:

```json
{
  "event_id": "00000000-0000-0000-0000-000000000001",
  "event_type": "invoice.paid",
  "occurred_at": "2026-09-24T12:00:00Z",
  "data": {
    "invoice_id": "inv_1"
  }
}
```

`POST /webhooks/events` responses:

- `202 Accepted` for a newly received event.
- `200 OK` for a duplicate `event_id`; `duplicate` is `true` and no second event is added.
- `401 Unauthorized` when the signature is missing, malformed, or invalid.
- `400 Bad Request` for an invalid event envelope after signature verification succeeds.

Example successful response:

```json
{
  "event_id": "00000000-0000-0000-0000-000000000001",
  "status": "received",
  "duplicate": false
}
```

Neither expected nor received signature values are returned in API errors.

Stage 2 uses an in-memory repository adapter only for the runnable API boundary. Database persistence, migrations, and database-enforced concurrent idempotency belong to Stage 3.

## Docker

```bash
docker compose up --build
```

## Configuration

```dotenv
APP_ENVIRONMENT=development
APP_HOST=0.0.0.0
APP_PORT=8000
APP_WEBHOOK_SECRET=replace-with-local-secret
APP_WEBHOOK_SIGNATURE_HEADER=X-Webhook-Signature
```

Tests explicitly disable real `.env` loading where configuration isolation is being tested, and Stage 2 tests use sample secrets only.

## Quality checks

Run the complete quality gate:

```bash
make check
```

Equivalent commands:

```bash
uv run ruff check src tests
uv run ruff format --check src tests
uv run pyright src tests
uv run pytest --cov=src --cov-report=term-missing
```

## Engineering rules

- Domain and application code do not depend on FastAPI or SQLAlchemy.
- Application use cases depend on explicit ports.
- HMAC verification uses the exact raw body and constant-time comparison.
- Untrusted HTTP input is validated at the boundary.
- Raw secrets and signatures are not logged or echoed.
- Tests mirror source structure where practical.
- No stage is merged until its quality gate and review are complete.

## Planned API

Available now:

- `GET /health`
- `POST /webhooks/events`

Later stages add:

- `GET /events/{event_id}`
- `GET /events?status=...`
- `POST /events/{event_id}/retry`

## License

A project license is planned for the final documentation/release stage.
