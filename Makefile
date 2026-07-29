SHELL := /bin/sh
DOCKER := docker
ifneq ($(shell command -v docker.exe 2>/dev/null),)
DOCKER := docker.exe
else ifeq ($(shell [ -x '/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe' ] && echo yes),yes)
DOCKER := "/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe"
endif
DC := $(DOCKER) compose
API := $(DC) exec -T api

.DEFAULT_GOAL := help
.PHONY: help setup build up down destroy migrate seed reseed generate-seed index dev logs ps psql \
        test test-api test-web test-integration lint lint-api lint-web fmt typecheck smoke

help:
	@printf '%s\n' \
		'  help               Show available targets' \
		'  setup              Build images, start services, apply migrations' \
		'  build              Build all images' \
		'  up                 Start every service in the background' \
		'  down               Stop services, keep volumes' \
		'  destroy            Stop services and delete volumes (drops the database)' \
		'  migrate            Apply pending SQL migrations to the app and test databases' \
		'  seed               Load the committed synthetic dataset' \
		'  reseed             Reload the synthetic dataset from scratch' \
		'  generate-seed      Regenerate the committed seed CSVs deterministically' \
		'  index              Build the semantic index' \
		'  dev                Start the full stack with hot reload' \
		'  logs               Tail logs for all services' \
		'  ps                 Show service status' \
		'  psql               Open a psql shell against the app database' \
		'  test               Run the default test suites' \
		'  test-integration   Run tests that require the real embedding service' \
		'  lint               Lint everything' \
		'  typecheck          Typecheck the Next.js app' \
		'  fmt                Auto-format the Python services' \
		'  smoke              Verify every service answers its health endpoint'

setup:
	@[ -f .env ] || (printf '%s\n' 'error: .env is required' >&2; exit 1)
	$(DC) build
	$(DC) up -d db embedding api
	$(DC) run --rm api python -m app.scripts.wait_for_dependencies
	$(MAKE) migrate

build:
	$(DC) build

up:
	$(DC) up -d

down:
	$(DC) down

destroy:
	$(DC) down -v

migrate:
	$(API) python -m app.scripts.migrate
	$(API) python -m app.scripts.migrate --database test

seed:
	$(API) python -m app.scripts.seed

reseed:
	$(API) python -m app.scripts.seed --force

generate-seed:
	python database/seed/generate.py --out database/seed/data

index:
	$(API) python -m app.scripts.index_clinical_documents

dev:
	$(DC) up

logs:
	$(DC) logs -f --tail=100

ps:
	$(DC) ps

psql:
	$(DC) exec db psql -U $${POSTGRES_USER:-clinical} -d $${POSTGRES_DB:-clinical_search}

test: test-api test-web

test-api:
	$(API) pytest -q

test-web:
	$(DC) run --rm --no-deps web pnpm test

test-integration:
	$(API) pytest -q -m integration

lint: lint-api lint-web

lint-api:
	$(API) ruff check app tests
	$(API) ruff format --check app tests

lint-web:
	$(DC) run --rm --no-deps web pnpm lint

typecheck:
	$(DC) run --rm --no-deps web pnpm typecheck

fmt:
	$(API) ruff check --fix app tests
	$(API) ruff format app tests

smoke:
	$(DC) exec -T api python -m app.scripts.smoke
