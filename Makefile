.PHONY: help lint test api web

help: ## List available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

lint: ## Run backend linting (ruff, import-linter)
	cd backend && uv run ruff check . && uv run ruff format --check . && uv run lint-imports

test: ## Run backend tests
	cd backend && uv run pytest

api: ## Run the backend dev server
	cd backend && uv run fastapi dev app/api/main.py

web: ## Run the frontend dev server
	cd web && pnpm dev
