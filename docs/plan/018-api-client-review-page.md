# T-018 Client review page

**Phase:** 3 · API · **Status:** analyzed · **Size:** M
**Refs:** R3.3, R6.5, R8.2, spec: Client journey, Data model Decision (token hash), API endpoints (Client)
**Depends on:** T-013, T-016

## Goal
Someone with the review link, and no account, sees the site's articles grouped by waiting/upcoming/published and can open one to read — the read side of the client journey, before approve/request-changes (T-019).

## Analysis

### Flow
1. `GET /review/{token}`: hash the path token, look up the site by `review_token_hash`. No match → 404 (never 403 — spec's decision, so a dead link can't be distinguished from one that never existed).
2. On match, group the site's articles: **waiting** = Awaiting approval; **upcoming** = Scheduled; **published** = Published. Draft/Changes requested/Failed are never shown to the client (spec: "Drafts, internal statuses... stay hidden").
3. `GET /review/{token}/articles/{id}`: same token check, then the article must be in one of the three visible statuses above — a Draft or Changes requested article's `id` guessed from elsewhere still 404s.
4. Both routes are rate-limited per client IP, trusting `X-Forwarded-For` only from the web service's own origin (spec's decision) — this ticket adds the rate limiter; trusting the header only from the web origin is enforced by only accepting the app's internal network path in deployment (Phase 5 concern), so locally this is a plain per-IP limiter with no origin check yet.

### API
`GET /review/{token}`

| Case | Status | Body |
| --- | --- | --- |
| Valid token | 200 | `{site_name, waiting: [ArticleCard], upcoming: [ArticleCard], published: [ArticleCard]}` |
| Unknown/reset token | 404 | `{code: "not_found"}` |
| Rate limited | 429 | `{code: "rate_limited"}` |

`ArticleCard`: `id`, `title`, `slug`, and for published only, `published_url`/publish date; for upcoming, `publish_at_utc`.

`GET /review/{token}/articles/{id}`

| Case | Status | Body |
| --- | --- | --- |
| Valid token, visible article | 200 | `{id, title, slug, body_html, version, status}` |
| Valid token, article not visible to client (Draft/Changes requested/Failed) or wrong site | 404 | `{code: "not_found"}` |
| Unknown token | 404 | `{code: "not_found"}` |

### Core
- `core/use_cases/review.py`: add `get_review_page(token)`, `get_review_article(token, article_id)`. Token lookup: hash the incoming token, compare to `site.review_token_hash` (constant-time compare, `hmac.compare_digest`).
- Status sync (T-021) isn't wired in yet — `upcoming`/`published` groups use the raw stored status for now; T-021 adds the WordPress check and sync warnings to this same route, since the spec requires "Runs the status check" here.

### Edge cases
| Case | Behavior |
| --- | --- |
| Token technically correct format but doesn't hash-match | 404, same as any unknown token |
| Article belongs to a different site than the token resolves to | Can't happen in the single-site MVP; no check needed yet (note for multi-site later) |

### Decisions
- Rate limiting: in-process token-bucket per IP (e.g. `slowapi` if already a dependency-light fit, else a small hand-rolled limiter — pick at implementation time per the ladder: stdlib first). No new dependency unless the hand-rolled version is clearly worse.

## Acceptance criteria
- [ ] A valid review link groups articles correctly into waiting/upcoming/published; Draft/Changes requested/Failed never appear.
- [ ] An unknown or reset token returns 404 (not 403) on both routes.
- [ ] Reading a specific article hides Draft/Changes requested/Failed articles even with a correct token and a real article id.
- [ ] Excessive requests from one IP get 429.
- [ ] Swagger and Postman updated.

## Tasks
- [ ] `core/use_cases/review.py`: add the two read functions, token hashing/compare.
- [ ] `api/routes/public_review.py`: both routes, no session dependency (token-only, per R8.2).
- [ ] Rate limiter wired into `public_review.py` only (agency routes stay session-gated, not IP-limited).
- [ ] Unit tests: grouping logic, hidden statuses, token mismatch.
- [ ] Integration test: Firestore emulator, real token round-trip (generate via T-016, verify via T-018).
- [ ] `pnpm gen:api`.

## Out of scope
- Approve / request changes (T-019).
- WordPress status sync and sync warnings (T-021).
- Trusting `X-Forwarded-For` only from the web origin (Phase 5 network-level concern).
