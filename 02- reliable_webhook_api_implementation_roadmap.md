# Reliable Webhook API — Implementation Roadmap

Repository: https://github.com/hamresan/reliable-webhook-api

Target stack: Python 3.12, FastAPI, SQLAlchemy, PostgreSQL (SQLite for focused tests), uv, Docker Compose, pytest, Ruff, and Pyright.

## Purpose

Build a small, production-minded API for receiving signed webhook events reliably. It must verify signatures, persist each event before processing, guarantee idempotent behaviour for duplicate deliveries, expose operational status, and retry only failures that are safe to retry.

The project is intentionally provider-neutral. Its first public contract supports one generic HMAC-signed event format; provider-specific adapters (for example Stripe or Shopify) are explicitly out of scope unless added later as a separate stage.

## Non-negotiable engineering rules

- Use Clean Architecture: domain and application code must not import FastAPI, SQLAlchemy, HTTP request types, or infrastructure configuration.
- Use dependency inversion: application use cases depend on explicit ports; database, clock, signature verifier, processor, and configuration are adapters.
- Keep modules small with a single responsibility. Do not create abstractions that have no real variation or test value.
- Validate untrusted HTTP input at the boundary. Never log raw secrets or signature values.
- Design state changes explicitly and make invalid state transitions impossible or rejected deterministically.
- Tests must mirror the source structure where practical.
- Unit tests never require Docker, a network connection, real credentials, or a live external service.
- Do not merge an incomplete stage. Every stage is implemented on its own branch, reviewed, passes all quality gates, and is merged before the next stage begins.

## Baseline quality gates

```bash
uv run ruff check src tests
uv run ruff format --check src tests
uv run pyright src tests
uv run pytest --cov=src --cov-report=term-missing
```

Minimum total line coverage is 90% after Stage 2; aim for 95%+ on domain and application layers.

## Suggested branch convention

```text
stage/00-project-foundation
stage/01-domain-and-ports
stage/02-event-receipt-and-idempotency
...
```

## Target behaviour and terminology

The first version exposes:

- POST /webhooks/events
- GET /events/{event_id}
- GET /events?status=...
- POST /events/{event_id}/retry
- GET /health

Suggested state model:

```text
received -> processing -> processed
                    \-> failed -> retry_scheduled -> processing
```

Duplicates are identified by a client-supplied event_id. A duplicate delivery must return a stable, successful response and must not cause a second processor execution. The raw payload is persisted only after signature verification succeeds.

## Stage 0 — Project foundation and developer experience

Branch: stage/00-project-foundation

### Deliverables

- Create a src/ layout and package namespace, tests/, pyproject.toml, lockfile, .gitignore, .env.example, Makefile, Dockerfile, and docker-compose.yml scaffold.
- Configure Python 3.12, FastAPI, Uvicorn, SQLAlchemy async support, Alembic, pytest, pytest-asyncio, HTTPX, Ruff, and Pyright.
- Add a minimal application factory and GET /health endpoint with no database dependency yet.
- Configure GitHub Actions to run formatting, linting, type checking, and tests.
- Update README only with commands that are already true at this stage; retain an honest development status.

### Required tests

- Unit test for application settings parsing and safe defaults.
- ASGI/API test that /health returns the documented response.
- A test proving test configuration does not read a real .env file or require secrets.

### Completion and merge gate

- make check runs all baseline quality commands successfully.
- Docker image builds successfully; the compose definition can start the API skeleton.
- CI is green and repository instructions are reproducible from a clean checkout.

## Stage 1 — Domain model, state machine, and application ports

Branch: stage/01-domain-and-ports

### Deliverables

- Define domain types: WebhookEvent, EventId, EventStatus, FailureReason, ProcessingAttempt, and event timestamps.
- Implement a state transition policy: accepted transitions, terminal state rules, retry eligibility, maximum-attempt policy, and deterministic domain errors.
- Define application ports for event repository, signature verification, clock, transaction boundary, and event processor.
- Define use-case input/output DTOs without HTTP or ORM types.
- Establish application error mapping vocabulary.

### Required tests

- Unit tests for every valid and invalid state transition.
- Boundary tests for retry count and terminal-state behaviour.
- Tests that domain objects reject empty IDs, invalid statuses, and invalid timestamps/attempt values.
- Architecture-import test proving the domain and application packages do not depend on FastAPI or SQLAlchemy.

### Completion and merge gate

- Domain/application coverage is at least 95% and tests document rules rather than implementation details.
- Public contracts are reviewed before persistence/API work begins.

## Stage 2 — Signature verification and request acceptance

Branch: stage/02-event-receipt-and-idempotency

### Deliverables

- Implement an HMAC-SHA256 verifier adapter using the original raw request bytes and a named signature header.
- Use constant-time comparison and fail closed when the secret/header is missing or malformed.
- Implement ReceiveWebhookEvent use case: verify first, validate event envelope, persist a newly received event, and return a duplicate result when the ID already exists.
- Define the generic request envelope contract: event_id, event_type, occurred_at, and data.
- Add POST /webhooks/events with accurate status codes and safe error messages.

### Required tests

- Unit tests for valid, invalid, malformed, and missing signatures; include known deterministic HMAC vectors.
- Use-case tests using in-memory repository/clock fakes.
- HTTP tests create a real signature from the exact bytes sent to the endpoint.
- Test that invalid signatures create no persisted event and no processor invocation.

## Stage 3 — Persistence, migrations, and transactional idempotency

Branch: stage/03-persistence-and-migrations

### Deliverables

- Add SQLAlchemy models and an Alembic migration for events and processing attempts.
- Store event ID with a database-enforced unique constraint.
- Implement repository and unit-of-work adapters.
- Provide PostgreSQL runtime configuration and SQLite test configuration only where feature-compatible.

### Required tests

- Integration tests against a real temporary database.
- Concurrency-oriented duplicate receipt test.
- JSON payload round-trip test.
- API integration tests using the real repository adapter and dependency wiring.

## Stage 4 — Processing orchestration and failure recording

Branch: stage/04-event-processing

### Deliverables

- Implement ProcessReceivedEvent use case.
- Define a deterministic sample processor.
- Separate processing business logic from HTTP receipt.
- Make repeated process commands safe.
- Add structured logs using event ID and state.

## Stage 5 — Retry policy and operational API

Branch: stage/05-retry-and-operations

### Deliverables

- Add a bounded exponential backoff retry policy.
- Implement a scheduling port.
- Implement retry, get event, and list events endpoints.
- Add a worker/CLI command that finds due retryable events and processes them safely.
- Return operational DTOs with sanitized failure summaries.

## Stage 6 — Docker, configuration, observability, and security hardening

Branch: stage/06-production-readiness

### Deliverables

- Complete Docker Compose setup for API, PostgreSQL, and optional local worker.
- Add explicit configuration validation.
- Add readiness check separated from liveness.
- Add correlation IDs, structured logs, and metrics-friendly hooks.
- Document secret handling, TLS expectation, payload-size limit, rate limiting, and retention.

## Stage 7 — Documentation, examples, and portfolio finish

Branch: stage/07-documentation-and-release

### Deliverables

- Rewrite README as a finished public-project document.
- Add docs/ with event lifecycle and signature format.
- Add runnable sample script.
- Add MIT License, contribution guidance, issue templates if useful, and v0.1.0 release notes.

## Pull request and merge checklist

- [ ] Branch contains only work for its assigned stage.
- [ ] Acceptance criteria are demonstrably complete.
- [ ] Ruff, format check, Pyright, and pytest pass locally and in CI.
- [ ] Coverage threshold is met.
- [ ] Tests mirror changed source layers.
- [ ] No provider-specific framework types leaked into domain/application packages.
- [ ] No secrets, private payloads, generated databases, or local environment files are committed.
- [ ] README/API documentation changed whenever externally visible behaviour changed.
- [ ] Final code review checks naming, cohesion, error handling, transaction boundaries, logging safety, and backwards compatibility.
- [ ] Only after the PR is approved and CI is green may the branch be merged into main.

## Explicit non-goals for v0.1.0

- Supporting every third-party webhook protocol.
- Guaranteed exactly-once side effects across external systems.
- A distributed queue or multi-region deployment.
- Authentication for operational endpoints.
- A dashboard frontend.
