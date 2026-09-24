# Release notes

## v0.1.0

Initial portfolio release of Reliable Webhook API.

### Highlights

- Provider-neutral signed webhook receipt using HMAC-SHA256.
- PostgreSQL-backed idempotent persistence with duplicate handling.
- Deterministic processing outcomes and persisted processing attempts.
- Bounded retry scheduling with retryable-failure classification and dead-letter state.
- Operational event lookup, filtering, pagination, and manual retry endpoint.
- Atomic retry claiming for concurrent workers.
- Docker Compose local environment with PostgreSQL and optional retry worker.
- Separate liveness and database readiness endpoints.
- Correlation IDs, structured request logging, metrics-friendly hooks, and request payload limits.
- Clean Architecture boundaries with unit, API, architecture, and PostgreSQL integration tests.

### Known limitations

- Operational endpoints are unauthenticated and require deployment/network protection where appropriate.
- TLS termination and rate limiting are expected at a reverse proxy or API gateway.
- The included metrics adapter is intentionally minimal; production monitoring can integrate a dedicated metrics/telemetry backend.
- The service does not claim exactly-once delivery across arbitrary downstream systems.
- Payload retention/deletion policy is deployment-specific.
