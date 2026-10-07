# T-027 API data layer

**Phase:** 4 · Frontend · **Status:** analyzed · **Size:** M
**Refs:** E1–E6, spec: API endpoints; architecture: Frontend (Rules)
**Depends on:** T-022 (report endpoint + regenerated types), T-026 (`createSession` / `logout` and the 401 redirect), T-031 (API: `siteId`-scoped routes), T-032 (site switcher — every agency route below lives under `/sites/{siteId}/...`)

## Goal
Every API endpoint the screens need has one typed query or mutation. All API integration lives in this ticket. Function names and signatures match T-033's fixture functions, so wiring a screen (T-032, T-028, T-029) is pointing its `modules/<m>/data.ts` at these instead of the fixtures.

## Analysis

### `siteId` threading
Every agency function below takes `siteId` as its first argument and calls `/sites/{siteId}/...` (T-031). `siteId` comes from the route segment T-032 adds (`app/sites/[siteId]/...`), read via Next's route params — not stored in a cookie or global. `revalidatePath` targets include the `siteId` segment (e.g. `/sites/${siteId}/articles`). The review module (client-facing, token-only) is unaffected — no `siteId` anywhere in it.

### Functions
Types come from `lib/api/schema.ts` only. Queries run in Server Components. Mutations are `"use server"`, return `MutationResult`, and call `revalidatePath` on the paths that show the changed data.

**`modules/sites/repository/`**

| Function | Endpoint | Error codes |
| --- | --- | --- |
| `listSites()` | `GET /sites` | — |
| `createSite(form)` | `POST /sites` | `wp_connection_failed` |

**`modules/articles/repository/`**

| Function | Endpoint | Revalidates | Error codes |
| --- | --- | --- | --- |
| `listArticles(siteId, status?)` | `GET /sites/{siteId}/articles?status=` | — | — |
| `getArticle(siteId, id)` | `GET /sites/{siteId}/articles/{id}` | — | `not_found` → `notFound()` |
| `getReviewLink(siteId)` | `GET /sites/{siteId}/review-link` | — | — |
| `pasteArticle(siteId, form)` | `POST /sites/{siteId}/articles/paste` | `/sites/{siteId}/articles` | `empty_content`, `payload_too_large` |
| `uploadArticles(siteId, formData)` | `POST /sites/{siteId}/articles/upload` (`postForm`) | `/sites/{siteId}/articles` | `no_files`, `too_many_files`, `payload_too_large`; per file: `unsupported_file_type`, `unreadable_file`, `file_too_large` |
| `updateArticle(siteId, id, form)` | `PATCH /sites/{siteId}/articles/{id}` | `/sites/{siteId}/articles`, same `+/{id}` | `not_editable`, `empty_update`, `empty_content`, `wordpress_error` |
| `sendForReview(siteId, id)` | `POST …/send-for-review` | same | `not_sendable` |
| `pullBack(siteId, id)` | `POST …/pull-back` | same | `not_awaiting_approval` |
| `scheduleArticle(siteId, id, publishAt)` | `POST …/schedule` | same + `/sites/{siteId}/report` | `not_schedulable`, `publish_at_in_past`, `wordpress_error` |
| `retryArticle(siteId, id)` | `POST …/retry` | same + `/sites/{siteId}/report` | `not_failed`, `wordpress_error` |
| `resetReviewLink(siteId)` | `POST /sites/{siteId}/review-link/reset` | `/sites/{siteId}/articles` | — |

**`modules/review/repository/`**

| Function | Endpoint | Error codes |
| --- | --- | --- |
| `getReview(token)` | `GET /review/{token}` | `not_found` → `notFound()`, `rate_limited` → thrown to `error.tsx` |
| `getReviewArticle(token, id)` | `GET /review/{token}/articles/{id}` | same |
| `approve(token, id, {client_name, version})` | `POST …/approve` | `article_changed`, `not_awaiting_approval`, `rate_limited`, `not_found` |
| `requestChanges(token, id, {client_name, comment, version})` | `POST …/request-changes` | same |

Review mutations revalidate `/review/{token}`.

**`modules/report/repository/`**: `getReport(siteId)` → `GET /sites/{siteId}/report`.

### Shared pieces
- `lib/error-messages.ts`: `messageFor(code)` maps every code above to one user-facing sentence, with a generic fallback. One place, so screens don't each invent wording.
- `components/local-time.tsx` (client): formats an ISO UTC string in the browser's timezone with `Intl.DateTimeFormat`. Server Components render in UTC, so dates must go through this. Skipped: a date library.
- `modules/articles/schemas/`:
  - `statusFilterSchema`: the 7 statuses or empty.
  - `articleFormSchema`: title required, slug optional and lowercase-hyphen, body HTML non-empty.
  - `scheduleSchema`: the `datetime-local` string converted to ISO with the browser's offset (`toIsoWithOffset`), so the API gets `publish_at` with a timezone (spec: Dates).
- `modules/review/schemas/decisionSchema`: name required, comment required for request changes.
- `next.config`: `experimental.serverActions.bodySizeLimit` set to `100mb`, which fits the API's upload limit (10 files × 10 MB, `server/app/api/routes/imports.py`).

### Edge cases
| Case | Behavior |
| --- | --- |
| API down / 500 | Mutation throws; the route's `error.tsx` shows it |
| Upload: some files fail | `ok: true` with per-file results; the UI shows each failure |
| 401 on any agency call | T-026's redirect, not a mutation result |
| `datetime-local` in the past | Client-side check plus API `publish_at_in_past` |

## Acceptance criteria
- [ ] Every agency and client endpoint in spec: API endpoints (except AI, P2) has exactly one function.
- [ ] No hand-written request/response types; `pnpm typecheck` passes.
- [ ] Each expected error code returns `{ ok: false, code }`; `messageFor` covers all of them.
- [ ] Unit test: `toIsoWithOffset` (two offsets, DST edge) and `messageFor` fallback.

## Tasks
- [ ] Wait for T-022 and T-031 to land; `make gen-api`.
- [ ] Sites, articles, review, report repositories.
- [ ] `lib/error-messages.ts`, `components/local-time.tsx`, zod schemas.
- [ ] `next.config` body size limit.
- [ ] Add a minimal test runner if none exists (`vitest`, one config) and the unit test.

## Out of scope
- UI (T-028, T-029). AI draft endpoints (Phase 7).
