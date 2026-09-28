.PHONY: help up down check fmt test lint typecheck migrate seed snapshot bench clean

PYTHON ?= python3
UV ?= uv

help:
	@echo "OpenPaperCheck Development Commands"
	@echo "==================================="
	@echo "  make check      - Run all linters, type checks, and tests"
	@echo "  make fmt        - Auto-format code with ruff"
	@echo "  make test       - Run pytest test suite"
	@echo "  make bench      - Run SQLite lookup speed benchmark"
	@echo "  make lint       - Run ruff linter and deny-list fairness checks"
	@echo "  make typecheck  - Run pyright static type analysis"
	@echo "  make up         - Start local Docker Compose services (db, api, web, worker)"
	@echo "  make down       - Stop Docker Compose services"
	@echo "  make migrate    - Run Alembic database migrations"
	@echo "  make seed       - Ingest sample Retraction Watch data"
	@echo "  make snapshot   - Build local SQLite snapshot (data-latest)"
	@echo "  make clean      - Clean cache and build artifacts"

check: lint typecheck test

fmt:
	cd backend && $(UV) run ruff format src tests
	cd backend && $(UV) run ruff check --fix src tests

lint:
	cd backend && $(UV) run ruff check src tests
	@echo "Checking for banned people-features in signals and ml..."
	@! grep -rn -E "\b(author|country|nationality|institution|affiliation)\b" backend/src/openpapercheck/signals/ backend/src/openpapercheck/ml/ 2>/dev/null || (echo "FAILED: Banned people features detected!" && exit 1)
	@echo "Fairness deny-list check passed."

typecheck:
	cd backend && $(UV) run pyright

test:
	cd backend && $(UV) run pytest -v tests/

up:
	docker compose up --build

down:
	docker compose down

migrate:
	docker compose exec api opc db migrate

seed:
	docker compose exec api opc ingest rw --sample

snapshot:
	cd backend && $(UV) run opc snapshot --sample

bench:
	cd backend && $(UV) run python tests/benchmark_storage.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf backend/build backend/dist backend/*.egg-info
