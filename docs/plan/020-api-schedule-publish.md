# T-020 Schedule, retry, and the WordPress publisher

**Phase:** 3 · API · **Status:** analyzed · **Size:** L
**Refs:** R4.1–R4.5, spec: WordPress integration (Calls), API endpoints (Agency)
**Depends on:** T-013, T-015, T-009 (WordPress publish check proved the connection)

## Goal
The agency sets a publish date on an Approved article and WordPress schedules it; changing the date or retrying a failed call reuses the same post; editing a Scheduled article (started in T-015) now actually moves the WordPress post to draft.

## Analysis

### Flow
1. `POST /articles/{id}/schedule`, body `{publish_at, timezone}` (or a single ISO datetime with offset — see Decisions). First time (`Approved → Scheduled`, no `wp_post_id` yet): `POST /wp-json/wp/v2/posts` with `title`, `content`, `slug`, `status: "future"`, `date_gmt` (converted from the agency's local time). Store the returned `id` as `wp_post_id`, `published_url` stays empty until actually published.
2. Changing only the date on an already-`Scheduled` article: `POST /wp-json/wp/v2/posts/{wp_post_id}` with just `date_gmt` (R4.5) — status stays `Scheduled`.
3. Re-scheduling after `Approved` again (resubmitted and re-approved): `POST /wp-json/wp/v2/posts/{wp_post_id}` with new `title`, `content`, `slug`, `status: "future"`, `date_gmt`.
4. **Edit-resets-Scheduled side effect (owed from T-015):** when `edit_article` (T-015) demotes a `Scheduled` article to `Draft`, it now also calls `Publisher.set_draft(wp_post_id)` → `POST /wp-json/wp/v2/posts/{id}` with `status: "draft"`. This ticket adds that call to T-015's use case (small cross-ticket edit, called out in T-015's Decisions).
5. **Timeout handling:** if the create call times out, the use case can't know whether WordPress made the post. Before treating it as failed, it calls `GET /posts?slug=…&status=future,draft,publish,private&context=edit`; if a post with the matching slug exists, reuse its id instead of creating a duplicate.
6. **Failure:** any non-timeout error, or a timeout where the slug lookup also fails, sets `Failed`, stores `last_error`, appends a `failed` event.
7. `POST /articles/{id}/retry`: only from `Failed`. Re-runs the same create-or-update logic as step 1–3 depending on whether `wp_post_id` is already set.

### API
`POST /articles/{id}/schedule`

| Field | Type | Rules |
| --- | --- | --- |
| `publish_at` | datetime (ISO 8601, with UTC offset) | required, future relative to server time |

| Case | Status | Body |
| --- | --- | --- |
| First schedule, from Approved | 200 | `ArticleDetail` (status `Scheduled`) |
| Date-only change, already Scheduled | 200 | `ArticleDetail` |
| Re-schedule after re-approval | 200 | `ArticleDetail` |
| From any other status | 409 | `{code: "not_schedulable"}` |
| `publish_at` in the past | 422 | `{code: "publish_at_in_past"}` |
| WordPress call fails | 200 with status `Failed` in the body (not an HTTP error — the request to *our* API succeeded; the article's own status reflects the WordPress failure) |

`POST /articles/{id}/retry`

| Case | Status | Body |
| --- | --- | --- |
| From Failed | 200 | `ArticleDetail` (now `Scheduled` or `Failed` again, same semantics as schedule) |
| From any other status | 409 | `{code: "not_failed"}` |

### Data changes
No new fields beyond T-013's `wp_post_id`, `published_url`, `last_error`, `publish_at_utc`.

### Core
- `core/ports/publisher.py`: `Publisher` Protocol — `create_scheduled(title, content, slug, date_gmt) -> PublisherPost`, `update_scheduled(wp_post_id, **fields)`, `set_draft(wp_post_id)`, `find_by_slug(slug) -> PublisherPost | None`. (`get_statuses` for the batch check belongs to T-021.)
- `core/use_cases/schedule.py`: `schedule(article_id, publish_at)`, `retry(article_id)`. Both encapsulate the create-vs-update branch and the timeout/slug-lookup fallback.
- `adapters/wordpress/publisher.py`: real `httpx` implementation — already proven to work end-to-end in T-009; this ticket formalizes it behind the port and adds `update_scheduled`/`set_draft`/`find_by_slug`, which T-009 didn't need.
- Timezone conversion: agency's local `publish_at` (tz-aware ISO datetime) → `date_gmt` is a pure function in `core/lib/` (e.g. `core/lib/dates.py: to_date_gmt`), independent of the WordPress adapter.

### Edge cases
| Case | Behavior |
| --- | --- |
| Create call times out, slug lookup finds nothing | `Failed`, `last_error: "wordpress_timeout"` |
| Create call times out, slug lookup finds the post | Reuse found id as `wp_post_id`, proceed as if create succeeded |
| WordPress returns 4xx (e.g. invalid slug) | `Failed`, `last_error` holds the upstream message, logged per architecture.md's Logging convention |
| Retry on an article that was never actually created (first create failed before any id was assigned) | Same as a first schedule — goes through the create path, not update |

### Decisions
- `publish_at` is sent as a single ISO datetime with a UTC offset (e.g. `2026-11-01T09:00:00+07:00`) rather than separate `publish_at`+`timezone` fields — the offset already disambiguates, and it's one field to validate instead of two that could disagree.

## Acceptance criteria
- [ ] Scheduling an Approved article for the first time creates a WordPress post with `status: future` and stores its id.
- [ ] Changing only the date on a Scheduled article updates `date_gmt` only, via the stored id, and keeps status Scheduled.
- [ ] A simulated WordPress timeout followed by a successful slug lookup reuses the found post instead of creating a duplicate.
- [ ] A WordPress failure sets Failed with a stored reason; Retry re-attempts and can succeed.
- [ ] Editing a Scheduled article (T-015's endpoint) moves the real WordPress post to draft — verified with the local WordPress container.
- [ ] Swagger and Postman updated.

## Tasks
- [ ] `core/ports/publisher.py`, `core/lib/dates.py`.
- [ ] `adapters/wordpress/publisher.py`: extend with `update_scheduled`, `set_draft`, `find_by_slug`.
- [ ] `adapters/testing/scripted_publisher.py`: scriptable responses, including a timeout simulation.
- [ ] `core/use_cases/schedule.py`.
- [ ] Wire `Publisher.set_draft` into T-015's `edit_article` use case.
- [ ] `api/routes/articles.py`: `POST /articles/{id}/schedule`, `POST /articles/{id}/retry`.
- [ ] Unit tests: create vs. update branch, timeout + slug-lookup fallback, failure/retry, with the scripted publisher.
- [ ] Integration test: local WordPress container — create, change date, move to draft, confirm via `GET /wp-json/wp/v2/posts/{id}`.
- [ ] `pnpm gen:api`.

## Out of scope
- The batched status check (T-021).
- Bulk scheduling by cadence (spec: Out of scope).
