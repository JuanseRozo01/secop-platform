.PHONY: install dev test lint check

install:
	pip install -r requirements-dev.txt

dev:
	uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

test:
	pytest

lint:
	ruff check .

check: lint test
