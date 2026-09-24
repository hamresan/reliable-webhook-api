# Reliable Webhook API

> A provider-neutral FastAPI service being built stage by stage to receive signed webhook events reliably.

**Current status:** Stage 0 — project foundation and developer experience.

The repository currently provides the Python project scaffold, FastAPI application factory, `GET /health`, configuration loading, automated tests, Docker scaffold, and CI quality checks. Webhook receipt, signature verification, persistence, processing, and retries are planned for later stages and are not implemented yet.

## Current architecture

```text
src/reliable_webhook_api/
├── config/
└── presentation/
    └── api/
        ├── app.py
        └── routes/
            └── health.py
```

Domain, application, and infrastructure layers will be introduced in later roadmap stages only when they have real responsibilities.

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
git checkout stage/00-project-foundation

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

## Docker

```bash
docker compose up --build
```

Then call:

```bash
curl http://localhost:8000/health
```

## Configuration

Stage 0 only uses these optional settings:

```dotenv
APP_ENVIRONMENT=development
APP_HOST=0.0.0.0
APP_PORT=8000
```

Tests explicitly disable `.env` loading, so they do not require real secrets or developer-local configuration.

## Quality checks

Run the complete Stage 0 quality gate:

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

## Roadmap

Implementation is split into independently reviewed stages:

1. Project foundation and developer experience
2. Domain model, state machine, and application ports
3. Signature verification, request acceptance, and idempotency
4. Persistence, migrations, and transactional idempotency
5. Processing orchestration and failure recording
6. Retry policy and operational API
7. Production readiness and security hardening
8. Documentation and v0.1.0 release

See [the implementation roadmap](./02-%20reliable_webhook_api_implementation_roadmap.md).

## Engineering rules

- Clean Architecture boundaries are introduced deliberately as responsibilities appear.
- Domain and application code must not depend on FastAPI or SQLAlchemy.
- Application code depends on explicit ports where there is meaningful variation or test value.
- Tests mirror source structure where practical.
- No stage is merged until its quality gate and review are complete.
- No raw secrets or webhook signatures are logged.

## Planned API

Only `GET /health` exists in Stage 0. Planned later endpoints include:

- `POST /webhooks/events`
- `GET /events/{event_id}`
- `GET /events?status=...`
- `POST /events/{event_id}/retry`

## License

A project license is planned for the final documentation/release stage.
