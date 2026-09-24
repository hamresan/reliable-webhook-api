# Reliable Webhook API

A provider-neutral FastAPI service for reliably receiving, persisting, inspecting, and retrying signed webhook events.

The project demonstrates a production-conscious webhook boundary built with Clean Architecture: exact-body HMAC verification, PostgreSQL-backed idempotency, deterministic processing, bounded retries, operational APIs, health checks, and Docker-based local execution.

## Features

- HMAC-SHA256 verification of exact request-body bytes.
- PostgreSQL persistence with unique `event_id` idempotency.
- Stable duplicate handling for sequential and concurrent delivery.
- Persisted processing attempts and sanitized failure metadata.
- Bounded exponential-backoff retries and dead-letter state.
- Atomic retry claiming for concurrent workers.
- Event lookup, filtering, pagination, and manual retry APIs.
- Separate liveness and database readiness endpoints.
- Request correlation IDs, structured request logs, and metrics-friendly hooks.
- Configurable request payload-size protection.
- Unit, API, architecture, and PostgreSQL integration tests.

## Architecture

```text
src/reliable_webhook_api/
├── domain/          # business concepts, state, retry and transition rules
├── application/     # use cases, DTOs, errors, and explicit ports
├── infrastructure/  # PostgreSQL, HMAC, processing, scheduling, workers, observability
├── presentation/    # FastAPI routes/middleware/dependencies and CLI entry points
└── config/          # validated runtime settings
```

Dependencies point inward: domain and application do not depend on FastAPI, SQLAlchemy, database sessions, or provider-specific infrastructure. Infrastructure implements application ports, while presentation performs HTTP/CLI mapping and dependency wiring.

See [Event lifecycle](docs/event-lifecycle.md) and [Webhook signature](docs/signature.md) for focused design documentation.

## Technology

Python 3.12, FastAPI, Uvicorn, SQLAlchemy async, asyncpg, PostgreSQL, Alembic, uv, Docker Compose, pytest, Ruff, and Pyright.

## Quick start

Requirements: Docker and Docker Compose.

Clone the repository, copy the sample environment, and start the stack:

```bash
git clone https://github.com/hamresan/reliable-webhook-api.git
cd reliable-webhook-api
cp .env.example .env
docker compose up --build
```

The local API is available at `http://localhost:8000`. The API container waits for PostgreSQL and applies Alembic migrations before starting Uvicorn.

Check liveness and readiness:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

Expected responses are `{"status":"ok"}` and `{"status":"ready"}`.

Send a correctly signed demo event and immediately inspect its stored status:

```bash
python examples/send_webhook.py
```

The script uses only the documented local sample secret by default. To target another local address or secret, set `WEBHOOK_BASE_URL` and `APP_WEBHOOK_SECRET`.

## Configuration

The sample `.env.example` contains placeholders only.

| Variable | Local default/example | Purpose |
| --- | --- | --- |
| `APP_ENVIRONMENT` | `development` | Runtime environment |
| `APP_HOST` | `0.0.0.0` | Application bind host outside Compose overrides |
| `APP_PORT` | `8000` | Published local API port |
| `APP_WEBHOOK_SECRET` | `replace-with-local-secret` | Shared HMAC secret |
| `APP_WEBHOOK_SIGNATURE_HEADER` | `X-Webhook-Signature` | Signature header name |
| `APP_DATABASE_URL` | local PostgreSQL URL | Async SQLAlchemy database URL |
| `APP_LOGGING_LEVEL` | `INFO` | Application logging level |
| `APP_MAX_PAYLOAD_BYTES` | `1048576` | Maximum accepted request payload |
| `APP_RETRY_MAX_ATTEMPTS` | `3` | Retry attempt bound |
| `APP_RETRY_BASE_DELAY_SECONDS` | `30` | Initial retry delay |
| `APP_RETRY_MAX_DELAY_SECONDS` | `3600` | Maximum retry delay |

Production configuration requires an explicit webhook secret and database URL. Invalid retry bounds fail settings validation.

## API

Interactive OpenAPI documentation is exposed by FastAPI at `/docs` while the application is running.

### Receive an event

`POST /webhooks/events`

Request envelope:

```json
{
  "event_id": "00000000-0000-0000-0000-000000000001",
  "event_type": "invoice.paid",
  "occurred_at": "2026-09-24T12:00:00Z",
  "data": {"invoice_id": "inv_1"}
}
```

The signature is the lowercase hexadecimal HMAC-SHA256 digest of the exact HTTP body bytes. See [signature documentation](docs/signature.md).

Responses: `202` for a new event, `200` with `duplicate: true` for an existing/concurrent duplicate, `401` for a missing/malformed/invalid signature, and `400` for an invalid envelope after successful signature verification.

### Operational endpoints

- `GET /health` — process liveness.
- `GET /ready` — database-backed readiness.
- `GET /events/{event_id}` — event status, attempts, timestamps, and sanitized failure metadata.
- `GET /events?status=failed&offset=0&limit=50` — filtered, paginated event list.
- `POST /events/{event_id}/retry` — schedule a retry when state and retry policy permit it.

## Idempotency

PostgreSQL uniqueness on `event_id` is the final authority. A duplicate event does not create another persisted event. Concurrent uniqueness conflicts are translated into the same stable duplicate application result rather than leaking database exceptions.

Idempotent receipt does not imply exactly-once effects in arbitrary downstream systems.

## Processing and retries

Events progress through explicit states including `received`, `processing`, `processed`, `failed`, `retry_scheduled`, and `dead_letter`.

Only explicitly classified retryable failures are scheduled. Backoff is bounded by configuration and cannot bypass state-transition rules. Invalid-signature requests are rejected before persistence and never enter retry processing. `processed` and `dead_letter` are terminal.

Run one due-retry worker pass locally with:

```bash
uv run python -m reliable_webhook_api.presentation.cli.retry_worker
```

Or run the optional worker continuously with Compose:

```bash
docker compose --profile worker up --build
```

## Database migrations

Production deployments should run migrations explicitly as a deployment step:

```bash
uv run alembic upgrade head
```

A fresh database can be created entirely from migration history. For a disposable development/test database:

```bash
uv run alembic downgrade base
```

## Testing

Install development dependencies:

```bash
uv sync --dev
```

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

The configured coverage gate is 95%. CI uses PostgreSQL for integration behaviour that depends on real transactions, uniqueness, JSON persistence, concurrency, migrations, and dependency wiring.

## Security and deployment assumptions

- HMAC comparison is constant-time and operates on exact body bytes.
- Raw secrets, signatures, and private payloads are not logged or echoed.
- Request size is bounded before webhook processing.
- Every response carries `X-Request-ID`; request logs contain correlation metadata rather than payload contents.
- TLS termination is expected at a trusted reverse proxy or ingress.
- Rate limiting should be enforced at the reverse proxy/API gateway.
- Operational endpoints are unauthenticated in v0.1.0 and require deployment/network protection where appropriate.
- Persisted payloads can contain business-sensitive data; deployments must define retention/deletion and backup policies.
- CORS is intentionally disabled because this release has no browser-frontend requirement.
- The local metrics adapter is a library-neutral hook, not a complete production monitoring stack.

## Limitations

This release is a focused reference implementation rather than a hosted webhook platform. It does not provide tenant/auth management, a dashboard, provider-specific webhook adapters, application-level rate limiting, public TLS termination, or exactly-once guarantees across external systems.

The sample event handlers demonstrate the processing boundary; real downstream business integrations must supply their own processor behaviour and operational controls.

## Project documents

- [Event lifecycle](docs/event-lifecycle.md)
- [Webhook signature](docs/signature.md)
- [Contributing](CONTRIBUTING.md)
- [v0.1.0 release notes](RELEASE_NOTES.md)
- [MIT License](LICENSE)

## License

MIT. See [LICENSE](LICENSE).
