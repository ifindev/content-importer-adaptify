# T-006 Compose: api and web

**Phase:** 2 · Local infra · **Status:** analyzed · **Size:** M
**Refs:** architecture: Infrastructure › Local setup
**Depends on:** T-002, T-004

## Goal
`make up` starts the API and web app in Docker with hot reload, and the web app can reach the API by service name.

## Analysis

### Decisions
- **Multi-stage Dockerfiles.** Each app gets a `dev` stage now. The `prod` stage comes in Phase 5, in the same file.
- **Source is bind-mounted** for hot reload. Dependencies stay inside the container: `backend/.venv` and `web/node_modules` are anonymous volumes, so host and container installs don't clash (macOS vs Linux binaries).
- **Service URLs:** the web container uses `API_URL=http://api:8000`. Host ports: api `8000`, web `3000`.
- **Env:** compose reads the root `.env` (copied from `.env.example`).

## Acceptance criteria
- [ ] `make up` starts `api` and `web`; `make down` stops them; `make logs` follows logs
- [ ] `http://localhost:8000/health` and `http://localhost:3000/articles` respond
- [ ] Editing a Python file reloads the API; editing a page reloads the web app
- [ ] A server-side call from the web container to `http://api:8000/health` succeeds (shown on a stub page or via `docker compose exec web`)
- [ ] Fresh clone: `cp .env.example .env && make up` works with no other steps

## Tasks
- [ ] `backend/Dockerfile` (dev stage: uv, `fastapi dev --host 0.0.0.0`)
- [ ] `web/Dockerfile` (dev stage: pnpm via corepack, `pnpm dev`)
- [ ] `docker-compose.yml` with `api` and `web`, volumes, env, ports
- [ ] `.dockerignore` for both apps
- [ ] Makefile targets: `up`, `down`, `logs`, `ps`
- [ ] `.env.example`: `API_URL`, `APP_ENV=local`

## Out of scope
- WordPress, MariaDB (T-007); Firebase emulators (T-008)
- Production images (Phase 5)
