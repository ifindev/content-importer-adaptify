# T-009 WordPress publish check

**Phase:** 2 · Local infra · **Status:** done · **Size:** M
**Refs:** spec: WordPress integration (Authentication, Calls, Status check); architecture: Server › Ports
**Depends on:** T-007

## Goal
Prove the riskiest link before building features on top of it: the API logs in to WordPress, creates a scheduled post, and sees it go live. This also starts the real `Publisher` port and adapter that Phase 3 builds on.

## Analysis

### Flow (integration test)
1. Create a post with `status: "future"` and `date_gmt` 3 seconds ahead, with sample HTML (headings, lists, links, bold, italic).
2. Wait until the time has passed, then call `wp-cron.php` over HTTP.
3. Run the batch status check for that post ID.
4. Expect `status: "publish"` and a `link`.
5. Fetch the post with `context=edit` and check that the HTML was stored intact.
6. Delete the post (cleanup).

### Port (first version)
`core/ports/publisher.py`, only what this ticket needs:

| Method | WordPress call |
| --- | --- |
| `check_credentials() -> None` | `GET /users/me?context=edit` |
| `create_scheduled(title, slug, html, publish_at_utc) -> int` | `POST /posts` with `status: "future"`, `date_gmt` |
| `get_statuses(post_ids) -> list[PostStatus]` | `GET /posts?include=…&status=publish,future,draft,private&_fields=id,status,link,date_gmt&context=edit&per_page=100` |

`PostStatus` (`id`, `status`, `link`, `date_gmt`) goes in `core/domain/models.py`. Errors raise `WordPressError` from `core/domain/errors.py` with the HTTP status and WordPress's error code. Updating posts, moving them back to draft, and lookup by slug come in Phase 3.

### Startup check
On startup (FastAPI lifespan), the API calls `check_credentials()`. On failure it logs a clear error naming `WP_BASE_URL` and `WP_USERNAME`, and **keeps running**. Per the spec, a WordPress outage shows as a banner; it doesn't crash the app.

### Edge cases
| Case | Behavior |
| --- | --- |
| `date_gmt` already in the past | WordPress publishes immediately. The test uses a future time so it really exercises cron. |
| `date_gmt` format | Send ISO 8601 without an offset (`2026-10-06T10:00:00`). WordPress reads `date_gmt` as UTC. |
| WordPress filters the HTML (kses) | The admin user has `unfiltered_html` on a single site, so content should be stored as-is. If not, record it in the spec risks. |
| Wrong password | `check_credentials` raises `WordPressError(401, "incorrect_password")`; the startup log says so. |

## Acceptance criteria
- [x] Integration test (marked `integration`, run with `make test-integration`) passes against local WordPress
- [x] Unit tests for the adapter's request building and error mapping using `httpx.MockTransport`
- [x] API startup logs "WordPress credentials OK" with good credentials, and a clear error with bad ones, without crashing
- [x] `Publisher` is wired in `container.py`; `core/` doesn't import `httpx` (import-linter passes)
- [x] Any behavior that differs from the spec's WordPress integration section is fixed in the spec (none needed — see Notes)

## Tasks
- [x] `core/ports/publisher.py`, `PostStatus`, `WordPressError`
- [x] `adapters/wordpress/publisher.py` with `httpx.AsyncClient`, Basic auth, timeouts
- [x] Settings: `WP_BASE_URL`, `WP_USERNAME`, `WP_APP_PASSWORD`
- [x] Lifespan credential check in `api/main.py`
- [x] `tests/fixtures/sample_article.html`
- [x] Unit tests (MockTransport) and the integration test
- [x] pytest marker `integration`; Makefile target `test-integration`

## Notes
- **Wrong-password error code differs from this ticket's own guess**, not from `docs/spec.md` (which never named a specific code): WordPress actually returns `rest_not_logged_in` for bad Basic-auth credentials on `/users/me?context=edit`, not `incorrect_password`. The adapter and startup log already use whatever code WordPress returns generically, so no code change was needed — noted here for the record only.
- **kses/`unfiltered_html` verified for real**, not just assumed: the integration test's `content.raw` check (step 5 of the Flow) passed, confirming the admin user's HTML is stored intact. No spec.md risk row added.
- **Found and fixed a pre-existing bug while making these tests work**: `Settings`'s `env_file=".env"` was relative to the process's current working directory, but every Makefile target runs from `server/`, where no `.env` exists — so `Settings()` silently fell back to empty defaults on every host-run invocation (`make test`, `make api`, etc.) since T-002. It only ever worked inside Docker, where `env_file:` in compose sets real process env vars and bypasses pydantic-settings' dotenv lookup entirely. Fixed by resolving the `.env` path relative to `settings.py`'s own location instead of cwd.
- **Added a service-to-service `WP_BASE_URL` override** for the `api` container in `docker-compose.yml`, mirroring `web`'s existing `API_URL` override from T-006 — `api`'s `.env`-sourced `WP_BASE_URL=http://localhost:8080` only makes sense for host-side test runs; inside the container it needs `http://wordpress`.
- Added `logging.basicConfig(level=logging.INFO)` in `api/main.py` — without it, the root logger defaults to `WARNING` and the "WordPress credentials OK" success log would never actually appear in `make logs`, even though it would still pass in a test using `caplog` (which overrides the level per-test). Verified the real difference by checking container logs before and after.

## Out of scope
- Article lifecycle, scheduling use case, sync warnings (Phase 3)
- Timeout retry with slug lookup (Phase 3)
- HTML cleaning with `nh3` (Phase 3, import)
