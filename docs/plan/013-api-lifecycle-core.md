# T-013 Lifecycle core: article model, Firestore repository, list and detail

**Phase:** 3 · API · **Status:** done · **Size:** L
**Refs:** R2.4, spec: Data model, Article lifecycle, API endpoints (Agency)
**Depends on:** T-012

## Goal
The domain model and the lifecycle rules exist as real code, the `Site`/`Article`/`Event` collections are readable and writable through Firestore, and the agency can list and open articles. Every later ticket (import, edit, review, schedule, sync, report) builds on this.

## Analysis

### Flow
1. At startup, `container.py` ensures the single `sites/{siteId}` document exists (created from `settings` if missing: `name`, `wp_base_url`; `review_token_hash`/`review_token_created_at` stay empty until T-016 resets the link).
2. `GET /articles` lists the site's articles, optionally filtered by `status`, newest first.
3. `GET /articles/{id}` returns one article with its `events` (history log) and open comment (comment itself ships with T-017/T-019; the field exists on the model now, empty until then).

### API
`GET /articles`

| Field | Type | Rules |
| --- | --- | --- |
| `status` (query) | string, optional | one of the seven statuses; omitted = all |

| Case | Status | Body |
| --- | --- | --- |
| OK | 200 | `{articles: [ArticleSummary]}` |

`GET /articles/{id}`

| Case | Status | Body |
| --- | --- | --- |
| Found | 200 | `ArticleDetail` (includes `events: [Event]`) |
| Not found | 404 | `{code: "not_found"}` |

Both routes require a session (T-012). Neither runs the WordPress status check yet — that's T-021; for now `sync_warning` is always `null` and `GET /articles` returns raw stored statuses.

### Data changes
New Firestore collections, per spec's Data model:
- `sites/{siteId}`: `name`, `wp_base_url`, `review_token_hash`, `review_token_created_at`.
- `sites/{siteId}/articles/{articleId}`: `title`, `slug`, `body_html`, `source`, `source_filename`, `warnings`, `status`, `sync_warning`, `version`, `approved_version`, `publish_at_utc`, `wp_post_id`, `published_url`, `last_error`, `last_checked_at`, `created_at`, `updated_at`.
- `sites/{siteId}/articles/{articleId}/events/{eventId}`: `type`, `actor`, `at`, `data`.

Single-site MVP: `siteId` is a fixed constant (e.g. `"default"`), not yet selectable — matches "One pre-configured WordPress site" in scope.

### Core
- `core/domain/models.py`: `Site`, `Article`, `Event` (Pydantic or dataclasses — Pydantic, for free validation and reuse in API schemas' internal mapping).
- `core/domain/statuses.py`: `Status` enum (the seven statuses), `SyncWarning` enum (`late`, `changed_in_wordpress`, `missing_in_wordpress`), `EventType` enum (all types listed in the spec's Data model table).
- `core/domain/lifecycle.py`: `ALLOWED_TRANSITIONS: dict[Status, set[Status]]` encoding the state diagram, and a `transition(article, to_status, actor) -> Article` helper that raises `core.domain.errors.NotAllowed` on an illegal move and appends an `Event`. Later tickets' use cases call this instead of hand-rolling status checks.
- `core/ports/article_repository.py`: `ArticleRepository` Protocol — `get_site`, `list_articles(status=None)`, `get_article(id)`, `create_article`, `save_article` (also appends the event), `list_events(article_id)`.
- `core/use_cases/`: no "list"/"get" use case file needed — these are pure reads with no business rule, so the route calls the repository directly (per the folder layout, use cases are "one file per user action"; reading isn't an action).
- `adapters/firestore/repository.py`: real implementation.
- `adapters/testing/`: in-memory implementation, used by every unit test from here on.

### Edge cases
| Case | Behavior |
| --- | --- |
| `GET /articles?status=bogus` | 422, FastAPI's own enum validation |
| Site document missing at startup | Created once from `settings.SITE_NAME`/`settings.WP_BASE_URL`; logged at INFO |

## Acceptance criteria
- [x] `Status`, `SyncWarning`, `EventType` enums match the spec exactly.
- [x] `lifecycle.transition` allows every arrow in the spec's state diagram and rejects every other move with `NotAllowed`.
- [x] `ArticleRepository` has both a Firestore and an in-memory adapter satisfying the same Protocol.
- [x] `GET /articles` and `GET /articles/{id}` work against the Firestore emulator.
- [x] `import-linter` passes with the new `core/` and `adapters/` code.
- [x] Swagger and Postman updated.

## Tasks
- [x] `core/domain/models.py`, `statuses.py`, `lifecycle.py`, `errors.py` (`NotAllowed`).
- [x] `core/ports/article_repository.py`.
- [x] `adapters/firestore/repository.py`, `adapters/testing/in_memory_repository.py`.
- [x] `api/routes/articles.py`: `GET /articles`, `GET /articles/{id}`.
- [x] `api/schemas.py`: `ArticleSummary`, `ArticleDetail`, `EventOut`.
- [x] Unit tests: every transition pair (status × target) from the state diagram, allowed and refused.
- [x] Integration tests: Firestore emulator round-trip for site bootstrap, article create/read, event append.
- [x] `pnpm gen:api` in `web/`.

## Implementation notes
- **Firestore client:** uses the raw `google.cloud.firestore.Client()`, not `firebase_admin.firestore.client()` as originally planned — the `firebase_admin` helper unconditionally resolves Application Default Credentials at construction time, ignoring `FIRESTORE_EMULATOR_HOST` entirely, which breaks local/emulator use. The raw client correctly switches to anonymous credentials when `FIRESTORE_EMULATOR_HOST`/`GOOGLE_CLOUD_PROJECT` are set.
- `container.py` falls back to `InMemoryArticleRepository` if Firestore client construction fails (mirrors the existing WordPress-credentials-check resilience: log an error, keep the API running), so a misconfigured/unreachable Firestore doesn't take down unrelated routes.

## Out of scope
- Creating articles (T-014), editing (T-015), status transitions beyond what's needed to prove `lifecycle.py` (T-015 onward exercise them through real use cases).
- WordPress status sync (T-021).
- Multi-site support.
