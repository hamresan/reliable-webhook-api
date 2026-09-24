# Contributing

Thanks for contributing to Reliable Webhook API.

## Development setup

Requirements: Python 3.12+, `uv`, Docker, and Docker Compose.

Install dependencies and start PostgreSQL as needed, then run the full quality gate before opening a pull request:

```bash
uv sync --dev
make check
```

## Engineering expectations

Keep domain and application code independent from FastAPI, SQLAlchemy, and provider-specific infrastructure. Depend on application ports at boundaries, keep mapping in dedicated mappers, and keep orchestration focused.

Tests should mirror the changed source layer. Add integration coverage when behaviour depends on PostgreSQL, persistence, concurrency, or real dependency wiring.

## Pull requests

Keep each pull request focused. Before requesting review:

- run Ruff lint and formatting checks;
- run strict Pyright;
- run the complete pytest suite and maintain the configured coverage threshold;
- update README or API documentation for externally visible behaviour;
- do not commit secrets, private webhook payloads, local databases, or generated environment files.

Bug reports and focused feature proposals are welcome through GitHub issues.
