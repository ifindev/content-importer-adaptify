# T-001 Repo layout

**Phase:** 1 · Bootstrap · **Status:** analyzed · **Size:** S
**Refs:** architecture: Backend › Folder layout
**Depends on:** none

## Goal
The repo has its top-level shape and shared files, so the backend and web tickets can start in parallel.

## Acceptance criteria
- [ ] Root has `README.md`, `CLAUDE.md`, `docs/`, `.gitignore`, `.env.example`, `Makefile`
- [ ] `.gitignore` covers Python (`.venv/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`), Node (`node_modules/`, `.next/`), env files (`.env`, `.env.*` except `.env.example`), and OS/editor files
- [ ] `make help` lists the available targets
- [ ] `.env.example` has a comment header explaining that later tickets add their variables

## Tasks
- [ ] Add `.gitignore`
- [ ] Add `.env.example` (header only)
- [ ] Add `Makefile` with a self-documenting `help` target (`## comment` after each target)

## Out of scope
- `backend/` and `web/` contents (T-002, T-003)
- `infra/` and `.github/` (created by the tickets that first need them; git doesn't keep empty folders)
