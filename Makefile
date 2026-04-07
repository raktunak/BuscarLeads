.PHONY: dev up down migrate test lint

dev:
	docker compose up --build

up:
	docker compose up -d

down:
	docker compose down

migrate:
	docker compose exec api alembic upgrade head

migrate-create:
	docker compose exec api alembic revision --autogenerate -m "$(msg)"

test:
	docker compose exec api pytest -v

lint:
	docker compose exec api ruff check app/
	docker compose exec api mypy app/

shell:
	docker compose exec api python -c "import IPython; IPython.start_ipython()" 2>/dev/null || docker compose exec api python

logs:
	docker compose logs -f api celery-worker
