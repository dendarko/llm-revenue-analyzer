.PHONY: install dev run test lint fmt

install:
	python -m pip install --upgrade pip
	pip install -e ".[dev]" || true

dev:
	uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000

run:
	uvicorn src.app.main:app --host 0.0.0.0 --port 8000

test:
	pytest -q

lint:
	ruff check .

fmt:
	ruff check . --fix
