.PHONY: setup lint format typecheck test migrate up down seed demo seed-local demo-local

setup:
	python -m pip install --upgrade pip
	python -m pip install -e ".[dev]"
	python -m pre_commit install

lint:
	python -m ruff check .

format:
	python -m ruff format .
	python -m ruff check . --fix

typecheck:
	python -m mypy src/llm_revenue_analyzer

test:
	python -m pytest

migrate:
	python -m alembic upgrade head

up:
	docker compose up -d --build

down:
	docker compose down -v

seed:
	docker compose run --rm api sh -lc "python -m alembic upgrade head && python -m llm_revenue_analyzer.scripts.seed"

demo:
	docker compose run --rm api sh -lc "uvicorn llm_revenue_analyzer.api.app:app --host 0.0.0.0 --port 8000 >/tmp/api.log 2>&1 & for i in 1 2 3 4 5 6 7 8 9 10; do curl -sf http://127.0.0.1:8000/health && break; sleep 1; done; python -m llm_revenue_analyzer.scripts.demo"

seed-local:
	python -m alembic upgrade head
	python -m llm_revenue_analyzer.scripts.seed

demo-local:
	python -m llm_revenue_analyzer.scripts.demo
