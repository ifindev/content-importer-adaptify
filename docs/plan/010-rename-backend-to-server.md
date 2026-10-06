# T-010 Rename backend to server

**Phase:** 2 · Local infra · **Status:** done · **Size:** S
**Refs:** architecture: Backend
**Depends on:** T-002

## Goal
`backend/` is renamed to `server/` everywhere, so `docs`, `server`, `web` sort alphabetically. No behavior change.

## Analysis

### Decisions
- Python package stays named `app` (it already was); only the directory and prose references move.
- `.venv` and caches are regenerated, not moved.

## Acceptance criteria
- [x] `server/` exists with the former `backend/` contents; `backend/` is gone
- [x] `make lint`, `make test`, `make api`, `make gen-api` work against `server/`
- [x] No remaining "backend" references in docs, Makefile, pyproject.toml, CLAUDE.md, README.md, .env.example (except incidental prose like "backend settings" describing concepts, reworded where it reads oddly)

## Tasks
- [x] `git mv backend server`
- [x] Update `Makefile`, `backend/pyproject.toml` description, `.env.example`, `CLAUDE.md`, `README.md`
- [x] Update `docs/architecture.md`, `docs/workflow.md`, `docs/spec.md`, `docs/plan/*.md`
- [x] Regenerate `.venv` under `server/` and confirm `make lint`/`make test` pass

## Out of scope
- Renaming the Python package `app` itself
- Any change to `web/`
