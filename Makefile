.PHONY: install run test unit-test integration-test coverage integration-coverage lint format format-check typecheck check ci-check migrate migrate-down up down

install:
	uv sync

run:
	uv run uvicorn reliable_webhook_api.presentation.api.app:app --reload

test:
	uv run pytest

unit-test:
	uv run pytest --ignore=tests/integration

integration-test:
	uv run pytest tests/integration

coverage:
	uv run pytest --ignore=tests/integration --cov=src --cov-report=term-missing --cov-fail-under=90

integration-coverage:
	uv run pytest tests/integration --cov=src --cov-append --cov-report=term-missing --cov-fail-under=95

lint:
	uv run ruff check src tests

format:
	uv run ruff format src tests

format-check:
	uv run ruff format --check src tests

typecheck:
	uv run pyright src tests

check: lint format-check typecheck coverage

ci-check: lint format-check typecheck
	uv run coverage erase
	uv run pytest --ignore=tests/integration --cov=src --cov-report= --cov-fail-under=0
	uv run pytest tests/integration --cov=src --cov-append --cov-report=term-missing --cov-fail-under=95

migrate:
	uv run alembic upgrade head

migrate-down:
	uv run alembic downgrade base

up:
	docker compose up --build -d

down:
	docker compose down --rmi local --remove-orphans
