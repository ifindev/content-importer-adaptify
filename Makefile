.PHONY: help lint test api web gen-api

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
