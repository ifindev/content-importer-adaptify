# T-037 Backend correctness fixes, and Unschedule

**Phase:** 4 · API · **Status:** done · **Size:** M
**Refs:** R2.2, R2.3, R4.3, R4.4, R5.1, R5.4, R8.2; spec: Article lifecycle, Approval rules, API endpoints
**Depends on:** T-031, T-034, T-036
**Improves:** T-015, T-020, T-021, T-034, T-018

> **Changed by T-039:** unschedule now trashes the WordPress post instead of moving it to draft, and a new date creates a new post. The draft-move wording below is the original decision.

## Goal
A spec-against-code audit (2026-10-08) found bugs that no ticket covered. This fixes them, and makes the lifecycle table the one source of truth for status changes. That table is where the decision to make Scheduled read-only came from.

## Analysis

### Fixes
| # | Bug | Fix |
| --- | --- | --- |
| 1 | Retry after a first-time schedule failure returned 500: the Failed article had no `publish_at_utc` | The Failed article keeps the requested date. Retry refuses a date that has passed (`publish_at_in_past`), and `schedule` accepts Failed, so the agency can set a new one. |
| 2 | Editing a Scheduled article saved Draft before WordPress confirmed the draft move, so a refusal left unapproved text scheduled | **Scheduled is read-only**, like Awaiting approval. To change it, the agency unschedules first (→ Approved), then edits (→ Draft). The edit path never calls WordPress. An approval reset also clears `approved_version`. |
| 3 | One status-check cache slot for every site, so opening site A skipped site B's check and showed A's result | `SyncCache` is keyed by site. |
| 4 | The client rate limit trusted any `X-Forwarded-For`; bad tokens were never limited, because the token lookup ran first | The web app sends `X-Client-IP` with `INTERNAL_API_SECRET`. The API trusts that IP only with the secret, otherwise it uses the socket address. The limit is a router dependency, so it runs before the token lookup. |
| 5 | Deleting a Draft that still owns a WordPress post (unscheduled, then edited) left the post behind | Delete moves the post to WordPress's trash first (`DELETE /posts/{id}`, recoverable). If WordPress refuses, nothing is deleted. |
| 6 | The status check read at most 100 posts | `get_statuses` asks in chunks of 100. |
| 7 | Leftovers | Site delete removes the review token from the secret store. Removed the unused `site_name` setting. |

### Lifecycle
`ALLOWED_TRANSITIONS` now matches what the use cases do, and `schedule.py` and `edit_article.py` go through `lifecycle.transition`:
- Scheduled → Published, **Approved** (unschedule), **Failed** (a date change WordPress refused). Scheduled → Draft is gone.
- Failed → Scheduled (Retry, or a new date).
- Staying in the same status (a date change, a retry that fails again) only records the event.

### API
`POST /sites/{siteId}/articles/{id}/unschedule`

| Case | Status | Body |
| --- | --- | --- |
| Scheduled | 200 | `ArticleDetail`, now Approved, with no `publish_at_utc` and the same `wp_post_id` |
| Any other status | 409 | `{"code": "not_scheduled"}` |
| WordPress refuses the draft move | 502 | `{"code": "wordpress_error"}`, nothing saved |

### Web
- Detail page:
  - Scheduled shows "Unschedule it to edit", with Unschedule and Change date.
  - Failed shows Set date next to Retry.
  - The approval-reset confirm covers Approved only.
- Each Scheduled row's menu has Unschedule.

## Acceptance criteria
- [x] Unit tests for each fix: retry after a first-time failure, retry past its date, schedule from Failed, a failed date change, unschedule (ok, WordPress refuses, wrong status, re-schedule reuses the post), Scheduled not editable, approval reset clears `approved_version`, per-site cache, client IP with and without the secret, delete trashes the post or keeps the article, chunked status check, review token delete.
- [x] Integration: unschedule moves the WordPress post to draft, and trash moves it to trash, against local WordPress.
- [x] Live: varying `X-Forwarded-For` no longer escapes the limit (20 × 404, then 429).

## Out of scope
- Moving the rate-limit buckets to a shared store (single instance for the MVP; see the `ponytail:` note in `api/rate_limit.py`).
- Confirming which `X-Forwarded-For` entry Cloud Run appends (Phase 5).
