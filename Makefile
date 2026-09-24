.PHONY: install run test lint format format-check typecheck check up down

install:
	uv sync

run:
	uv run uvicorn reliable_webhook_api.presentation.api.app:app --reload

test:
	uv run pytest --cov=src --cov-report=term-missing

lint:
	uv run ruff check src tests

format:
	uv run ruff format src tests

format-check:
	uv run ruff format --check src tests

typecheck:
	uv run pyright src tests

check: lint format-check typecheck test

up:
	docker compose up --build -d

down:
	docker compose down --rmi local --remove-orphans
