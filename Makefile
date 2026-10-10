.PHONY: install sync test lint run demo doctor serve collect build send schedule migrate docker-build docker-up

install:
	uv sync --group dev || python -m venv .venv && .venv/Scripts/activate && pip install -e ".[dev]" || pip install -e .

sync:
	uv sync --group dev

test:
	uv run pytest -q || pytest -q

lint:
	uv run ruff check . || ruff check .

run:
	uv run newsletter-machine run || newsletter-machine run

demo:
	uv run newsletter-machine run --demo || newsletter-machine run --demo

doctor:
	uv run newsletter-machine doctor || newsletter-machine doctor

collect:
	uv run newsletter-machine collect --platforms blogs --limit 5 --since-hours 168 || newsletter-machine collect --platforms blogs --limit 5 --since-hours 168

build:
	uv run newsletter-machine build --since-hours 168 || newsletter-machine build --since-hours 168

send:
	uv run newsletter-machine send --newsletter $(ID) || newsletter-machine send --newsletter $(ID)

serve:
	uv run uvicorn newsletter_machine.api.main:app --reload || uvicorn newsletter_machine.api.main:app --reload

schedule:
	uv run newsletter-machine schedule || newsletter-machine schedule

migrate:
	uv run alembic upgrade head || alembic upgrade head

docker-build:
	docker build -t newsletter-machine:latest .

docker-up:
	docker compose up --build
