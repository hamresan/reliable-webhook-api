# Reliable Webhook API

> A provider-neutral FastAPI service being built stage by stage to receive signed webhook events reliably.

**Current status:** Stage 5 — bounded retries and operational API.

The service accepts and persists generic signed webhook events, records deterministic processing outcomes, and exposes operational inspection and bounded manual retry scheduling. PostgreSQL remains the idempotency authority.

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
│   │   └── models/
│   └── security/
└── presentation/
    └── api/
        ├── dependencies/
        ├── routes/
        └── schemas/
```

Domain and application remain independent from FastAPI, SQLAlchemy, database sessions, and infrastructure configuration. ORM models are mapped to domain objects inside the persistence adapter and never escape through application ports.

## Technology stack

- Python 3.12
- FastAPI and Uvicorn
- SQLAlchemy async + asyncpg
- PostgreSQL
- Alembic
- uv
- Docker / Docker Compose
- pytest and HTTPX
- Ruff
- Pyright

## Local development

Copy the example environment file and set a local webhook secret:

```bash
cp .env.example .env
```

Start PostgreSQL and the API:

```bash
docker compose up --build
```

For local Docker only, the API container waits for PostgreSQL and runs `alembic upgrade head` before starting Uvicorn. The API is available at `http://localhost:8000`.

### Explicit migrations

Production deployments must run migrations explicitly as a deployment step; application startup does not run migrations itself.

```bash
uv run alembic upgrade head
```

Rollback all migrations in a disposable local/test database:

```bash
uv run alembic downgrade base
```

A fresh database is bootstrapped entirely from the Alembic migration history.

### Health check

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## Webhook receipt

Configure:

```dotenv
APP_WEBHOOK_SECRET=replace-with-local-secret
APP_WEBHOOK_SIGNATURE_HEADER=X-Webhook-Signature
APP_DATABASE_URL=postgresql+asyncpg://webhook:webhook@localhost:5432/webhook
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

- `202 Accepted` for a newly persisted event.
- `200 OK` for an existing or concurrently duplicated `event_id`; `duplicate` is `true`.
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

Database integrity errors are contained by the persistence adapter. A unique `event_id` conflict is translated to the stable duplicate application result; database exceptions are not exposed by the HTTP API.

## Persistence model

`webhook_events` stores the event ID, event type, JSON payload, occurred/received timestamps, status, sanitized failure metadata, version, and update timestamp. `processing_attempts` stores attempt number, processing timestamps, and sanitized failure metadata linked to the event.

PostgreSQL is the runtime and integration-test database. SQLite may be used only for isolated tests where its behavior is feature-compatible; concurrency and transactional idempotency tests intentionally run against PostgreSQL.

## Testing

CI starts a real PostgreSQL service, applies the Alembic migration from a fresh schema, and runs repository, concurrency, JSON round-trip, and real-wiring API integration tests.

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

- Domain and application code do not depend on FastAPI, SQLAlchemy, or infrastructure.
- Application use cases depend on explicit ports.
- Persistence mapping is isolated from use-case orchestration.
- HMAC verification uses exact raw body bytes and constant-time comparison.
- Database uniqueness is the final authority for concurrent idempotency.
- Raw secrets, signatures, and private payloads are not logged or echoed.
- Tests mirror source structure and integration boundaries.
- No stage is merged until its quality gate and review are complete.

## Operational API

Available now:

- `GET /health`
- `POST /webhooks/events`
- `GET /events/{event_id}` — inspect status, attempts, timestamps, and sanitized failure metadata.
- `GET /events?status=failed&offset=0&limit=50` — filter and paginate operational events.
- `POST /events/{event_id}/retry` — schedule an allowed retry for a failed retryable event.

Retry scheduling uses bounded exponential backoff. The default configuration allows three attempts, starts at 30 seconds, and caps the delay at one hour:

```dotenv
APP_RETRY_MAX_ATTEMPTS=3
APP_RETRY_BASE_DELAY_SECONDS=30
APP_RETRY_MAX_DELAY_SECONDS=3600
```

Only explicitly classified failure codes are retryable. Invalid-signature requests are rejected before persistence and therefore cannot enter the retry flow. Processed and dead-letter events are terminal and manual retry does not bypass state rules.

A scheduled retry is persisted as `retry_scheduled` with `next_retry_at`. Run due retries locally with:

```bash
uv run python -m reliable_webhook_api.presentation.cli.retry_worker
```

The worker selects only due scheduled events and processes them through the same application processing command. External exactly-once side effects cannot be guaranteed by HTTP alone; the service guarantees one effect invocation per successful internal claim.

## License

A project license is planned for the final documentation/release stage.
