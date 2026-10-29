.PHONY: install test run build clean

install:
	uv sync
	cd frontend && npm install

test:
	uv run pytest

run:
	uv run uvicorn backend.app.main:app --reload --port 8000

build:
	cd frontend && npm run build

clean:
	rm -rf data/*.sqlite3* data/tmp/* frontend/dist
