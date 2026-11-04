.PHONY: start test fixtures
start:
	uv sync --extra dev
	uv run python scripts/generate_fixtures.py
	uv run uvicorn src.api:app --host 127.0.0.1

test:
	uv sync --extra dev
	uv run python scripts/generate_fixtures.py
	uv run pytest -q

fixtures:
	uv run python scripts/generate_fixtures.py
