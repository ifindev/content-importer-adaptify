# T-021 WordPress status sync

**Phase:** 3 · API · **Status:** done · **Size:** M
**Refs:** R5.1–R5.4, spec: Sync warnings, WordPress integration (Status check)
**Depends on:** T-020

## Goal
Opening the articles table, the review page, or the report checks every Scheduled article against WordPress in one request, surfaces Late/Changed/Missing warnings without touching the stored status, and caches the result so repeat loads don't hammer WordPress.

## Analysis

### Flow
1. One function, `sync_statuses(site_id)`, collects every article currently `Scheduled` (plus `Published` articles not checked in the last 24h, per the spec's decision to recheck published posts at most once a day), and calls `GET /wp-json/wp/v2/posts?include=...&status=publish,future,draft,private&_fields=id,status,link,date_gmt&context=edit&per_page=100`.
2. Map each result per the spec's table (future/ahead → stays Scheduled; publish → Published + `published_url`; future/passed → Scheduled + Late; draft/private → keep status + Changed in WordPress; missing from the reply → keep status + Missing in WordPress).
3. A `publish` result **does** change the stored status (`Scheduled → Published`) and appends a `published` event — this is the one case where the sync check writes a real lifecycle transition, not just a warning. Every other mapping only sets `sync_warning`, never the status.
4. Request failure (network/timeout): change nothing, return a flag the caller uses to show "Can't reach WordPress" (R5.3) — never raises past the use case.
5. Cache: an in-process TTL cache (e.g. a dict keyed by `site_id` with a timestamp), one minute (R5.4, P1). `GET /articles`, `GET /review/{token}`, and `GET /report` all call the same cached `sync_statuses`, so three loads inside one minute cost one WordPress request, not three.

### API
No new routes. This modifies the response of three existing/later ones:
- `GET /articles` (T-013): each `ArticleSummary` gains `sync_warning: "late" | "changed_in_wordpress" | "missing_in_wordpress" | null`, and a top-level `wordpress_unreachable: bool`.
- `GET /review/{token}` (T-018): same `sync_warning` field on `ArticleCard`, same top-level flag.
- `GET /report` (T-022): consumes the same sync pass for its Needs attention block.

### Core
- `core/ports/publisher.py`: add `get_statuses(wp_post_ids) -> list[PublisherPostStatus]` (`id`, `status`, `link`, `date_gmt`).
- `core/use_cases/sync_status.py`: `sync_statuses(site_id) -> SyncResult` (`warnings_by_article_id`, `unreachable: bool`), including the one-minute cache and the 24-hour published-recheck throttle. A `Clock` port call (already in architecture.md's ports table) drives both time checks, so tests control time instead of sleeping.
- The mapping table itself is a pure function (`map_wp_status(our_status, wp_result, now) -> (new_status | None, warning | None)`), unit-testable without any adapter.

### Edge cases
| Case | Behavior |
| --- | --- |
| No Scheduled or recently-unchecked-Published articles exist | Skip the WordPress call entirely — zero-length `include` list means nothing to check |
| WordPress returns an id not in our `include` list (shouldn't happen, but) | Ignored — only requested ids are mapped |
| Cache hit mid-TTL, but an article was just scheduled (new `wp_post_id`) by a concurrent request | Acceptable staleness for the MVP — one-minute cache is a product decision already in the spec (R5.4), not a bug |

## Acceptance criteria
- [x] A Scheduled article whose WordPress post is now `publish` becomes Published with the live URL, and a `published` event is recorded.
- [x] A Scheduled article still `future` but past its date shows Late without changing status.
- [x] A Scheduled article now `draft`/`private` in WordPress shows Changed in WordPress without changing status.
- [x] A Scheduled article whose post is missing from the WordPress reply shows Missing in WordPress without changing status.
- [x] A WordPress request failure changes nothing and flags `wordpress_unreachable`.
- [x] Two calls to `GET /articles` inside one minute trigger only one WordPress request.
- [x] Swagger updated for the new response fields on `GET /articles` and `GET /review/{token}`.

## Tasks
- [x] `core/ports/publisher.py`: `get_statuses`. Already implemented since T-009 — nothing to add.
- [x] `adapters/wordpress/publisher.py`: implement `get_statuses`. Already implemented since T-009 — nothing to add.
- [x] `core/use_cases/sync_status.py`: mapping function, cache, published-recheck throttle.
- [x] Wire into `GET /articles` (T-013) and `GET /review/{token}` (T-018) routes.
- [x] Unit tests: the full mapping table from the spec, cache hit/miss, 24h throttle, with a fixed `Clock` and scripted publisher.
- [x] Integration test: local WordPress container — schedule a post, change it to draft directly via the WP admin REST call, confirm the next `GET /articles` shows Changed in WordPress.
- [x] `pnpm gen:api`.

### Deviations from the analysis above
- Dropped the `sync_statuses(site_id)` parameter — `ArticleRepository` is already single-site (no `site_id` anywhere in its interface), so the use case takes `(repository, publisher, clock, cache)` instead.
- Simplified away the proposed `SyncResult(warnings_by_article_id, unreachable)` return shape. `Article.sync_warning` and `Article.last_checked_at` already exist as persisted fields on the domain model (added in an earlier ticket), so `sync_statuses` writes the warning straight onto each article via the existing `repository.save_article` and returns just `SyncResult(unreachable: bool)`. Routes re-list articles as normal afterward — the warning rides along on the article they already fetch.
- The one-minute cache is a small `SyncCache` class (not a `Protocol`/port — it's single-process internal state, not an adapter boundary) held as a new field on `Container` and shared by both routes via `Depends`, so `/articles` and `/review/{token}` loads within the same minute share one WordPress request.
- `GET /articles`'s response, previously an ad-hoc `dict[str, list[ArticleSummary]]`, is now the named `ArticlesOut` model (`articles`, `wordpress_unreachable`) — brings it in line with every other route's typed response and gives the new flag a proper OpenAPI type.

## Out of scope
- A background job / polling (spec's decision: check only on page load).
- The report's own rendering of the Needs attention block (T-022).
