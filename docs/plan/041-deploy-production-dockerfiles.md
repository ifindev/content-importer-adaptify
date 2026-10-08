# T-041 Production Dockerfiles

**Phase:** 5 · Deploy · **Status:** done · **Size:** S
**Refs:** architecture: Infrastructure, Deployment and CI
**Depends on:** —

## Goal
Both apps have small production images that start fast and run on Cloud Run. The deploy workflow (T-045) builds these images.

## Analysis

### Today
- `server/Dockerfile` and `web/Dockerfile` have only a `dev` stage, each with a `TODO(Phase 5)` note for the prod stage.
- Server dev runs `fastapi dev … --port 8000` with reload. Web dev runs `pnpm dev`.
- `docker-compose.yml` builds both with `target: dev`. That stays.

### Server: `prod` stage
- `FROM python:3.12-slim AS prod`, copying the uv binary as the dev stage does (`COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /uvx /bin/`).
- Copy `pyproject.toml` and `uv.lock` first, then `uv sync --locked --no-dev --no-install-project`, then copy `app/`, then `uv sync --locked --no-dev --no-editable`. Dependency layers stay cached when only code changes.
- `ENV PYTHONUNBUFFERED=1` so logs reach Cloud Logging immediately.
- Run as a non-root user.
- `CMD` in shell form so `$PORT` expands: `fastapi run app/api/main.py --host 0.0.0.0 --port ${PORT:-8080}`. `fastapi[standard]` (already a dependency) ships `fastapi run`: uvicorn without reload.
- Check `server/.dockerignore` excludes `.venv`, `.ruff_cache`, `.import_linter_cache`, `.pytest_cache`, `tests/` and any local secret files.

### Web: `deps` → `build` → `prod`
- `web/next.config.ts`: add `output: "standalone"`. Next then emits a minimal `server.js` with only the needed `node_modules`.
- `deps`: `node:22-slim`, corepack with `pnpm@12.9.1` (as in dev), copy `package.json`, `pnpm-lock.yaml`, `pnpm-workspace.yaml`, `pnpm install --frozen-lockfile`.
- `build`: copy the source, then `pnpm build`, with these build args turned into env vars:
  - `NEXT_PUBLIC_FIREBASE_API_KEY`, `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN`, `NEXT_PUBLIC_FIREBASE_PROJECT_ID`.
  - `NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_URL` is **not** set. `lib/firebase-client.ts:17-22` connects to the emulator whenever it has any value.
  - These values are inlined into the browser bundle at build time, so one image belongs to one Firebase project.
- `prod`: `node:22-slim`, non-root user, `NODE_ENV=production`, `HOSTNAME=0.0.0.0`. Copy `.next/standalone`, `.next/static` to `.next/static`, and `public/`. `CMD ["node", "server.js"]`. `server.js` reads `PORT`, which Cloud Run sets.
- Runtime env (set by Terraform, not baked in): `API_URL`, `APP_ENV`, `INTERNAL_API_SECRET`.

### `API_URL` at build time
`lib/api-server.ts:8-14` and `modules/auth/repository/auth.mutations.ts:8-14` throw at module load when `API_URL` is unset. If `next build` loads those modules while collecting page data, the build fails in CI and in Docker.
- First try the build without `API_URL`.
- If it fails, move each check into a small function called on first use, so a missing `API_URL` still fails loudly at runtime. Don't pass a fake `API_URL` build arg: it would hide a missing runtime value.

### Request size limit
`next.config.ts` sets `serverActions.bodySizeLimit: "100mb"` for `.docx` uploads. Cloud Run rejects HTTP/1 request bodies over 32 MiB before they reach Next, with a bare 413.
- ~~Lower it to `"30mb"`.~~ Done differently: over the limit, the action throws on the client and the error boundary replaces the page. Instead, `bodySizeLimit` is `"31mb"` (1 MB for multipart overhead, still under 32 MiB) and the upload screen refuses a total over 30 MB before sending, with `upload_too_large`.
- Check the upload screen's error for a too-large request. If it shows a generic error, map it to a clear message ("Files are too large. Upload fewer files at a time, up to 30 MB in total.").
- Update spec.md or architecture.md if either mentions the 100 MB limit.

### Edge cases
| Case | Behavior |
| --- | --- |
| `PORT` not set (local `docker run`) | Server falls back to 8080; Next's `server.js` falls back to 3000. Pass `-e PORT=8080` to match Cloud Run. |
| Upload over 30 MB in total | Refused by Next with the app's error message, not a Cloud Run 413. |
| Image built without `NEXT_PUBLIC_FIREBASE_*` | Login fails in the browser. CI passes placeholders; deploy (T-045) passes the real values. |

## Acceptance criteria
- [x] `docker build --target prod server/` and `docker build --target prod web/` (with the Firebase build args) both succeed.
- [x] Image sizes noted in the ticket. Rough targets: server under 250 MB, web under 300 MB. Not a hard gate.
- [x] Both prod images run against the local compose stack (`docker run --network <compose network> -e PORT=8080 …`, pointing at the emulators):
  - [x] `GET /health` on the server returns `{"status":"ok"}`.
  - [x] The web login page renders, and login works against the Auth emulator. For this check only, build a local image with the emulator URL arg set.
  - [x] A paste import works end to end.
- [x] A `.docx` upload just over 30 MB shows the app's own error message.
- [x] `make up` still uses the dev stages and works as before.
- [x] `pnpm typecheck` and `make lint` green.

## Tasks
- [x] Server `prod` stage and `.dockerignore` check.
- [x] `output: "standalone"` and the web `deps`/`build`/`prod` stages.
- [x] Try `next build` without `API_URL`; make the check run on first use if it fails.
- [x] Lower `bodySizeLimit` to `30mb` and check the too-large error message.
- [x] Run both images locally as above; note the image sizes here.
- [x] Update docs that mention the upload limit.

## Results
- Image sizes (native arm64 build, amd64 is about the same): server 75 MB compressed, about 225 MB unpacked; web 94 MB compressed, about 265 MB unpacked.
- `next build` failed without `API_URL`. `lib/api-server.ts` now exports `apiUrl()`, read on use. `auth.mutations.ts` uses it too instead of its own copy of the check.
- Server: uv is bind-mounted for the `uv sync` steps only, so it isn't shipped. `CMD ["sh", "-c", "exec fastapi …"]` makes uvicorn PID 1 so it gets Cloud Run's SIGTERM; the plain shell form left `sh` as PID 1.
- `server/.dockerignore` also excludes `scripts/`.
- Local builds: BuildKit timed out loading registry metadata until the base images were pulled with `docker pull` first.

## Out of scope
- Distroless or Alpine base images.
- Multi-arch builds. Cloud Run is amd64. On an Apple Silicon Mac, local test builds use `--platform linux/amd64` or the native arch; CI builds amd64.
