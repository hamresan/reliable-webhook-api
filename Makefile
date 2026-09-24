.PHONY: install run test coverage lint format format-check typecheck check migrate migrate-down up down

install:
	uv sync

run:
	uv run uvicorn reliable_webhook_api.presentation.api.app:app --reload

test:
	uv run pytest

coverage:
	uv run pytest --cov=src --cov-report=term-missing

lint:
	uv run ruff check src tests

format:
	uv run ruff format src tests

format-check:
	uv run ruff format --check src tests

typecheck:
	uv run pyright src tests

check: lint format-check typecheck coverage

migrate:
	uv run alembic upgrade head

migrate-down:
	uv run alembic downgrade base

up:
	docker compose up --build -d

down:
	docker compose down --rmi local --remove-orphans
