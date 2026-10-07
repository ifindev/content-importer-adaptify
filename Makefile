.PHONY: help lint test api web gen-api up down logs ps firebase-reset

help: ## List available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

lint: ## Run server and web linting
	cd server && uv run ruff check . && uv run ruff format --check . && uv run lint-imports
	cd web && pnpm lint && pnpm format:check && pnpm typecheck

test: ## Run server tests
	cd server && uv run pytest

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
