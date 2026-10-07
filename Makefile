.PHONY: help lint test test-integration api web gen-api up down logs ps firebase-reset agency-user wp-setup wp-cron wp-reset

help: ## List available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

lint: ## Run server and web linting
	cd server && uv run ruff check . && uv run ruff format --check . && uv run lint-imports
	cd web && pnpm lint && pnpm format:check && pnpm typecheck

test: ## Run server and web unit tests (no external services needed)
	cd server && uv run pytest -m "not integration"
	cd web && pnpm test

test-integration: ## Run server integration tests (needs `make up` + `make wp-setup`)
	cd server && uv run pytest -m integration --log-cli-level=INFO

api: ## Run the API dev server
	cd server && uv run fastapi dev app/api/main.py

web: ## Run the frontend dev server
	cd web && pnpm dev

gen-api: ## Generate TypeScript types from the FastAPI schema
	cd server && uv run python scripts/export_openapi.py
	cd web && pnpm gen:api

up: ## Start api and web in Docker (detached, rebuilds on change)
	docker compose up --build -d

down: ## Stop and remove containers
	docker compose down

logs: ## Follow logs from all services
	docker compose logs -f

ps: ## List running services
	docker compose ps

firebase-reset: ## Clear emulator data (Firestore + Auth)
	docker compose stop firebase
	docker compose run --rm --entrypoint sh firebase -c "rm -rf /data/*"

agency-user: ## Create the one agency account in the Auth emulator (idempotent; re-run after firebase-reset)
	set -a && . ./.env && set +a && \
	code=$$(curl -s -o /tmp/agency-user.json -w "%{http_code}" \
	  "http://localhost:9099/identitytoolkit.googleapis.com/v1/accounts:signUp?key=$$NEXT_PUBLIC_FIREBASE_API_KEY" \
	  -H "Content-Type: application/json" \
	  -d "{\"email\":\"$$AGENCY_EMAIL\",\"password\":\"$$AGENCY_PASSWORD\",\"returnSecureToken\":true}") && \
	{ [ "$$code" = "200" ] || grep -q EMAIL_EXISTS /tmp/agency-user.json; } || \
	  { echo "Failed to create agency user:"; cat /tmp/agency-user.json; exit 1; }

wp-setup: ## One-time local WordPress install + application password (writes to .env)
	./infra/wordpress/local-setup.sh

wp-cron: ## Trigger WordPress's scheduler once (publishes any due scheduled posts)
	docker compose exec wordpress curl -s -o /dev/null -w "%{http_code}\n" http://localhost/wp-cron.php

wp-reset: ## Wipe the local WordPress and database volumes for a clean reinstall
	docker compose rm -sf wordpress mariadb
	docker volume rm -f $$(docker volume ls -q --filter label=com.docker.compose.volume=wordpress-data) \
	                   $$(docker volume ls -q --filter label=com.docker.compose.volume=mariadb-data)
