.PHONY: install dev test test-live lint check

install:
	pip install -r requirements-dev.txt

dev:
	uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

test:
	pytest

test-live:
	RUN_LIVE_TESTS=1 pytest -m live -s

lint:
	ruff check .

check: lint test
