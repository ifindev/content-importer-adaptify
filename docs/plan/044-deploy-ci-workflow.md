# T-044 CI workflow

**Phase:** 5 · Deploy · **Status:** in progress · **Size:** S
**Refs:** architecture: Deployment and CI; workflow: Definition of Done
**Depends on:** —

## Goal
Every push and pull request to `main` is checked automatically: server lint, import rules and unit tests, web lint, types, tests and build, and generated API types that match the server.

## Analysis

### Today
- There is no `.github/` directory.
- `make lint` runs, for the server: `ruff check`, `ruff format --check`, `lint-imports`; and for the web: `pnpm lint`, `format:check`, `typecheck`.
- `make test` runs `pytest -m "not integration"` and `pnpm test`.
- `make test-integration` runs `pytest -m integration`. It needs the Firestore emulator and the local WordPress, so it stays local.
- `make gen-api` runs `server/scripts/export_openapi.py`, which imports the FastAPI app and writes `web/lib/api/openapi.json` without a running server, then `pnpm gen:api` writes `web/lib/api/schema.ts`. Both files are committed.

### `.github/workflows/ci.yml`
- `on: push` (branches `main`) and `pull_request`.
- `concurrency: { group: ci-${{ github.ref }}, cancel-in-progress: true }`.
- `permissions: contents: read`.

**Job `server`** (`ubuntu-latest`, `working-directory: server`):
1. `actions/checkout`.
2. `astral-sh/setup-uv` with caching; Python version from `server/.python-version`.
3. `uv sync --locked`.
4. `uv run ruff check .`, `uv run ruff format --check .`, `uv run lint-imports`.
5. `uv run pytest -m "not integration"`.

**Job `web`** (`ubuntu-latest`, `working-directory: web`):
1. `actions/checkout`.
2. `pnpm/action-setup` (reads `packageManager`: pnpm 12.9.1).
3. `actions/setup-node` with Node 22 and `cache: pnpm`.
4. `pnpm install --frozen-lockfile`.
5. `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`.
6. `pnpm build` with placeholder `NEXT_PUBLIC_FIREBASE_*` values (any string). T-041 makes sure the build doesn't need `API_URL`.

**Job `api-types`** (needs both toolchains):
1. Checkout, setup-uv, `uv sync --locked` in `server/`, pnpm and Node, `pnpm install --frozen-lockfile` in `web/`.
2. `make gen-api`.
3. `git diff --exit-code web/lib/api/`. If the server changed the API and the types weren't regenerated, this fails and shows the diff.

The three jobs run in parallel.

### Keeping CI and Make in sync
The commands mirror `make lint` and `make test`. Calling `make` directly would mix server and web steps in one job, so the jobs list the commands. A comment at the top of `ci.yml` says "mirror the Makefile's lint and test targets".

### Edge cases
| Case | Behavior |
| --- | --- |
| Lockfile out of date | `uv sync --locked` or `pnpm install --frozen-lockfile` fails. That's the intended signal. |
| `APP_ENV` in tests | Unit tests already set what they need; CI sets nothing extra. |
| `.env` missing in CI | `settings.py` reads the repo-root `.env` only if it exists. Unit tests don't need it. Check on the first run. |

### Decisions
- Integration tests stay local (`make test-integration`) and are run by hand before a deploy that touches adapters. Running them in CI needs the Firebase emulators and WordPress as service containers: possible later, not needed now.
- Update architecture "Deployment and CI": what CI checks, and that integration tests are local.

## Acceptance criteria
- [ ] A push to `main` runs `server`, `web` and `api-types`, and all three pass.
- [ ] A pull request runs the same three jobs.
- [ ] On a throwaway branch: a failing unit test turns `server` red; an edited `schema.ts` turns `api-types` red; a type error turns `web` red. Delete the branch after.
- [ ] A second push while a run is in progress cancels the older run.
- [x] architecture.md updated.

## Tasks
- [x] Write `.github/workflows/ci.yml` with the three jobs.
- [ ] Push and fix anything that only shows up in CI (missing `.env`, cache keys, Python version).
- [ ] Run the three red checks on a throwaway branch.
- [x] Update architecture "Deployment and CI".

## Results
- Checked locally without `.env`: unit tests pass and `make gen-api` leaves `web/lib/api/` unchanged.
- `ruff format --check` failed on `main` for `app/adapters/documents/parser.py` and `app/api/routes/imports.py`. Both are reformatted in this change so CI starts green.
- `actionlint` passes.

## Out of scope
- Integration tests in CI.
- The deploy job (T-045).
- Branch protection rules. Work goes straight to `main` during the MVP.
- Dependabot or Renovate.
