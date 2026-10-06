# T-004 Frontend setup

**Phase:** 1 · Bootstrap · **Status:** done · **Size:** M
**Refs:** architecture: Frontend › Rules
**Depends on:** T-003

## Goal
The web app has all its tooling and the shared `lib/` and `hooks/` pieces the architecture describes, so Phase 4 can build modules without setup work.

## Analysis

### Decisions
- **`HttpClient` errors:** a non-2xx response throws `ApiError(status, code, data)`. `code` is read from the FastAPI error body. The mutation helpers turn known codes into `{ ok: false, code }` (see architecture: expected errors are returned).
- **`postForm`** sends `FormData` and does **not** set `Content-Type`, so `fetch` adds the multipart boundary.
- **`api-server.ts`** reads `API_URL` from env and fails fast at startup if it's missing. It forwards the `session` cookie and the client IP (`x-forwarded-for` from the incoming request headers) on every call.
- **`bodySizeLimit`:** `10mb` in `next.config.ts` (several `.docx` files per upload).

## Acceptance criteria
- [x] shadcn initialized; `components/ui/button.tsx` added and rendered on one stub page as a smoke test
- [x] Prettier (with `prettier-plugin-tailwindcss`) and `eslint-config-prettier` configured; `pnpm format:check` passes
- [x] `pnpm typecheck` (`tsc --noEmit`) passes
- [x] `lib/http.ts`, `lib/api-server.ts`, `lib/types/page-props.ts`, `lib/query-string.ts`, `lib/mutation-result.ts`, `hooks/use-filter-params.ts` exist and follow the architecture doc
- [x] Importing `lib/api-server.ts` from a `"use client"` file fails the build (checked once, then reverted)
- [x] `API_URL` added to `.env.example`

## Tasks
- [x] `pnpm dlx shadcn@latest init`; add `button`
- [x] Add `zod`, `server-only`; dev: `prettier`, `prettier-plugin-tailwindcss`, `eslint-config-prettier`
- [x] Scripts: `format`, `format:check`, `typecheck`
- [x] Write the `lib/` and `hooks/` files
- [x] `next.config.ts`: `experimental.serverActions.bodySizeLimit`
- [x] Makefile `lint` target also runs the web lint, format check, and typecheck

## Out of scope
- Real queries and mutations (Phase 4)
- Login flow (Phase 4)
