.PHONY: install migrate dev seed test lint format up down sync lambda-zip

install:
	cd backend && pip install -e ".[dev]"

migrate:
	cd backend && alembic upgrade head

dev:
	cd backend && uvicorn app.main:app --reload

seed:
	cd backend && python -m ingestion.seed_demo

test:
	cd backend && pytest -q

lint:
	cd backend && ruff check . && ruff format --check .

format:
	cd backend && ruff check --fix . && ruff format .

up:
	docker compose up --build

down:
	docker compose down

sync:
	cd backend && python -m ingestion.sync

lambda-zip:
	./scripts/package_lambda.sh
