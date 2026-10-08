# T-031 Multi-site: sites collection, siteId-scoped routes, encrypted credentials

**Phase:** 3 · API · **Status:** done · **Size:** L
**Refs:** spec: Data model, Out of scope ("Client site setup and WordPress connection"), R8.1 (unchanged)
**Depends on:** T-013, T-009 (WordPress publish check — its connectivity logic is reused here)

## Goal
An agency can create and list several client sites instead of operating against one hard-coded site. `sites/{siteId}` stops being a singleton created from config at startup (`SITE_ID = "default"` in `server/app/container.py:21`) and becomes a real collection the agency populates. Every article-scoped route (list, detail, edit, send for review, schedule, sync, report) moves under `/sites/{siteId}/...`. The agency login itself stays single and shared (R8.1 is not reopened) — this ticket is purely about how many client sites that one login can operate.

## Analysis

### Decisions (settled before writing this ticket, via `/grill-me`)
- **One shared agency login, many sites** — no per-user accounts or per-client access control.
- **Sites are created through the API** (`POST /sites`), not config files — each site brings its own WordPress base URL and app password.
- **WordPress connection is tested at creation time**, reusing T-009's connectivity check, before the site is persisted.
- **The WordPress app password is stored encrypted on the site document** in Firestore (not a per-site Secret Manager entry) — symmetric encryption with a key from the existing secret store / Secret Manager.
- **Routing is `siteId` in the path** (`/sites/{siteId}/articles`), not a session-bound "current site" — lets the agency have two clients open in separate tabs.
- **No migration**: today's single `"default"` site is local/demo data only; it's fine to drop and recreate sites from scratch once this ships.
- **No site removal/archive, no cross-site report rollup, no duplicate-base-URL guard** — out of scope for this pass.

### Flow
1. `POST /sites` — agency submits `name`, `wp_base_url`, `wp_username`, `wp_app_password`. The route calls the existing WordPress connectivity check (T-009) against those exact credentials. On failure: `422 {code: "wp_connection_failed"}`, nothing persisted. On success: generate a `siteId`, encrypt the app password, create the `sites/{siteId}` document, and reset its review token (same token-generation logic T-016 already has, just no longer tied to startup).
2. `GET /sites` — lists every site (`id`, `name`, `wp_base_url`; never the credential) for the switcher.
3. Every route from T-014 onward that currently assumes the single site now takes `siteId` from the path and resolves that site's repository/credentials instead of the `SITE_ID` constant.

### API
`POST /sites`

| Field | Type | Rules |
| --- | --- | --- |
| `name` | string | required |
| `wp_base_url` | string (URL) | required |
| `wp_username` | string | required; HTTP Basic auth needs the user an application password belongs to |
| `wp_app_password` | string | required, never echoed back |

| Case | Status | Body |
| --- | --- | --- |
| Created | 201 | `{id, name, wp_base_url}` |
| WP connection failed | 422 | `{code: "wp_connection_failed"}` |

`GET /sites`

| Case | Status | Body |
| --- | --- | --- |
| OK | 200 | `{sites: [{id, name, wp_base_url}]}` |

**Reparented routes** (unchanged behavior, new prefix): `GET/POST /sites/{siteId}/articles`, `GET /sites/{siteId}/articles/{id}`, and every other existing article/review/schedule/sync/report route from T-014–T-022. Not found on an unknown `siteId` → `404 {code: "site_not_found"}` before the existing per-article 404s apply. The client-facing review routes (token-based, no session) are unaffected — a review token is already scoped to one site.

### Data changes
- `sites/{siteId}`: add `wp_app_password_encrypted`. Drop the "one document, created from config at startup" note — it's now agency-created via the API.
- No change to `articles`, `events` shape; they just live under a non-singleton parent.

### Core
- `core/ports/article_repository.py`: methods that assumed a bound `site_id` (set at construction, per `adapters/firestore/repository.py:13`) take `site_id` per call instead, or the repository is constructed per-request from the route's path param.
- New `core/ports/site_repository.py` (or extend the existing repository): `create_site`, `list_sites`, `get_site(site_id)`.
- New `core/ports/wordpress_connection_checker.py` (if T-009's check isn't already a reusable port): same WordPress REST ping T-009 uses for the configured site, callable with arbitrary `(base_url, app_password)`.
- New `adapters/crypto/` (or similar): symmetric encrypt/decrypt for the app password, keyed from the existing secret store (local) / Secret Manager (GCP) — same place the review-token/WP-credential story already lives per spec's Data model decision note.
- `container.py`: remove `SITE_ID` constant; repositories/use cases become per-request, parameterized by the path's `siteId`.

### Edge cases
| Case | Behavior |
| --- | --- |
| `POST /sites` with unreachable/wrong WP credentials | `422 {code: "wp_connection_failed"}`, nothing written |
| Route with unknown `siteId` | `404 {code: "site_not_found"}` |
| `GET /sites` with zero sites | `200 {sites: []}` — empty state, not an error |

### Open questions
- Encryption key source (Secret Manager key vs. local-dev equivalent) — implementation detail, resolve while building, not a product decision.

### Follow-ups raised by the design (T-033), built here
- The Add Site design has a **Test connection** button separate from submit. Proposal: `POST /sites/test-connection` with the same body minus `name`; `200` or `422 {code: "wp_connection_failed"}`, persists nothing, reuses the same checker.
- The Sites list and switcher show each site's **connection status** and **article / needs-attention counts**. Proposal: store the last check result on the site (`connection_ok`, `connection_checked_at`, set on create and on test), and have `GET /sites` return it plus `article_count` and `needs_attention_count` computed from stored statuses, no live WordPress call.
- Built in this ticket (decided 2026-10-08). `GET /sites` also returns `wp_username` so the edit dialog can prefill it. A second endpoint, `POST /sites/{siteId}/test-connection`, tests the **stored** details (the sites-row button, and the edit dialog where an empty password means the stored one). Body fields override the stored ones, and only a test of exactly what is stored records `connection_ok`/`connection_checked_at`. Counts are computed per request, one article read per site (`ponytail:` note in `api/routes/sites.py`).

## Acceptance criteria
- [x] `POST /sites` tests the WordPress connection before persisting; failure leaves no document behind.
- [x] The stored app password is encrypted at rest; no endpoint ever returns it in plaintext.
- [x] Every existing article/review/schedule/sync/report route works unchanged in behavior, now under `/sites/{siteId}/...`, against the Firestore emulator with 2+ sites coexisting.
- [x] `SITE_ID` constant and startup-seeding of a single site are removed.
- [x] Unit tests: `create_site` (success, WP check failure), repository operations scoped correctly per `siteId` (one site's articles never leak into another's list).
- [x] Swagger and `pnpm gen:api` updated. ~~Postman collection~~: dropped, the repo has none and Swagger covers it.

## Tasks
- [x] `core/ports/site_repository.py`, `core/ports/wordpress_connection_checker.py` (or reuse/extend T-009's).
- [x] `adapters/crypto/`: encrypt/decrypt helper for the app password.
- [x] `adapters/firestore/repository.py`: `siteId`-parameterized reads/writes, `create_site`, `list_sites`.
- [x] `adapters/testing/in_memory_repository.py`: same multi-site shape for tests.
- [x] `api/routes/sites.py`: `POST /sites`, `GET /sites`.
- [x] Reparent `api/routes/articles.py` and every other Phase 3 router under `/sites/{siteId}/...`.
- [x] Remove `SITE_ID` constant and startup site-seeding from `container.py`.
- [x] Unit + integration tests updated for the new path shape and multi-site isolation.
- [x] `pnpm gen:api` in `web/`.
- [x] Follow-ups: `POST /sites/test-connection`, `POST /sites/{siteId}/test-connection`, connection fields and counts on `GET /sites`, with unit tests.

## Out of scope
- Site removal/archive (add + list only).
- Cross-site report rollup — Report stays per-site.
- Per-user accounts or per-client access control — R8.1 stands.
- Duplicate `wp_base_url` validation.
- The UI (site switcher, Add Site screen) — that's T-032, which depends on this ticket.
