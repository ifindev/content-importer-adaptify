# T-005 API type generation

**Phase:** 1 · Bootstrap · **Status:** done · **Size:** S
**Refs:** architecture: Frontend › Types come from the API
**Depends on:** T-002, T-004

## Goal
One command turns the FastAPI schema into TypeScript types for the web app, so the frontend never hand-writes API types.

## Analysis

### Decisions
- **No running server needed.** A script imports the FastAPI app and writes `app.openapi()` to a file. Faster and works in CI.
- **Both files are committed:** `web/lib/api/openapi.json` and `web/lib/api/schema.ts`. Reviewers see API changes in the diff. A CI check that they're up to date comes in Phase 5.
- **One command for both steps:** `make gen-api` runs the export, then `pnpm gen:api`.

## Acceptance criteria
- [x] `make gen-api` writes `web/lib/api/openapi.json` and `web/lib/api/schema.ts`
- [x] `schema.ts` contains the `/health` path and its response type
- [x] A typed call compiles: `api.get<paths["/health"]["get"]["responses"]["200"]["content"]["application/json"]>("/health")`
- [x] Running `make gen-api` twice in a row produces no diff
- [x] `schema.ts` is excluded from ESLint and Prettier

## Tasks
- [x] `server/scripts/export_openapi.py` (sorted keys, stable output)
- [x] Add `openapi-typescript` to web dev dependencies; script `gen:api`
- [x] Optional helper type in `lib/api/types.ts` to shorten response type lookups
- [x] Makefile target `gen-api`
- [x] Ignore `lib/api/schema.ts` in ESLint and Prettier configs

## Out of scope
- CI drift check (Phase 5)
