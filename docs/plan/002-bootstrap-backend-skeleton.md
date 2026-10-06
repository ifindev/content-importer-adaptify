# T-002 Backend skeleton

**Phase:** 1 · Bootstrap · **Status:** done · **Size:** M
**Refs:** architecture: Backend (Folder layout, Import rules)
**Depends on:** T-001

## Goal
A FastAPI app in `backend/` with the hexagonal folder structure, settings, and the composition root. Lint, the import rules, and tests run from day one, so the structure can't erode.

## Analysis

### Decisions
- **uv** manages Python 3.12 (`.python-version`) and dependencies (`pyproject.toml`, `uv.lock`).
- **Packages only, no empty ports.** Create the `core/` and `adapters/` packages so import-linter has something to check. Each port is added by the first ticket that needs it (T-009 adds `Publisher`), with its real methods. Empty `Protocol` stubs written now would just be guesses.
- `container.py` builds a `Container` dataclass from `Settings`. It starts with only `clock`; later tickets add adapters.
- `APP_ENV` = `local | gcp | test`. Settings load from env vars and an optional `.env`.

### import-linter contracts
Translate the import rules table into contracts in `pyproject.toml`:
- **Layers:** `app.api` → `app.core.use_cases` → `app.core.ports` → `app.core.domain`
- **Forbidden:** `app.core` must not import `app.adapters`, `app.api`, `httpx`, `google.cloud`, `firebase_admin`, `mammoth`, `nh3`, `langchain*`
- **Forbidden:** `app.adapters` must not import `app.core.use_cases` or `app.api`
- **Forbidden:** `app.api` must not import `app.adapters` (only `app.container` does)

## Acceptance criteria
- [x] `uv run fastapi dev app/api/main.py` serves `GET /health` → `{"status": "ok"}`
- [x] `/docs` shows Swagger
- [x] `make lint` runs `ruff check`, `ruff format --check`, and `lint-imports`, and all pass
- [x] `make test` runs pytest; one test covers `/health` via `TestClient`
- [x] A deliberate forbidden import (e.g. `import httpx` in `app/core/domain`) makes `lint-imports` fail. Remove it afterwards.

## Tasks
- [x] `uv init` in `backend/`, pin Python 3.12, add `fastapi[standard]`, `pydantic-settings`; dev: `ruff`, `pytest`, `import-linter`
- [x] Folders with `__init__.py`: `app/core/{domain,ports,use_cases,prompts,lib}`, `app/adapters/testing`, `app/api/routes`
- [x] `app/settings.py`, `app/container.py`, `app/core/ports/clock.py` + `SystemClock` adapter + `FixedClock` test adapter
- [x] `app/api/main.py` with the app factory, container in `app.state`, `/health` route
- [x] ruff config (line length, rule set) and import-linter contracts in `pyproject.toml`
- [x] `tests/unit/test_health.py`
- [x] Makefile targets: `lint`, `test`, `api` (run dev server)

## Out of scope
- Dockerfile (T-006)
- Firestore, WordPress, auth (T-008, T-009, Phase 3)
