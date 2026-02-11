.PHONY: migrate revert makemigration

build:
	docker compose build

migrate:
	docker compose run --rm migrator sh -c "alembic upgrade head"

revert:
	docker compose run --rm migrator sh -c "alembic downgrade -1"

makemigration:
	docker compose run --rm migrator sh -c 'alembic revision --autogenerate'

unittest:
	docker compose run --rm api pytest -vv .
	docker compose down
