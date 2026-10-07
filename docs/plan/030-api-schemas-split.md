# T-030 Split api/schemas.py by route

**Phase:** 3 · API · **Status:** done · **Size:** S
**Refs:** architecture: Server folder layout (schemas.py → schemas/ package)

## Goal
`server/app/api/schemas.py` has grown to 22 Pydantic classes across six unrelated concerns (auth, articles, imports/uploads, publishing, client review, the agency report) in one flat ~225-line file. After this ticket, it's a package with one module per route, so finding or adding a schema means opening the one file that owns it, not scanning the whole list.

## Analysis

### Current state
Every class in `schemas.py` is used by exactly one route file, with two classes shared by two routes:

- `api/routes/auth.py` → `SessionRequest`
- `api/routes/articles.py` → `EventOut`, `ArticleSummary`, `ArticleDetail`, `ArticlesOut`, `ScheduleRequest`, `ArticleUpdate`
- `api/routes/imports.py` → `ArticlePaste`, `UploadFileResult`, `UploadResponse`, plus reuses `ArticleSummary`, `ArticleDetail`, `EventOut` from the articles group (`imports.py` already imports `get_clock`/`get_document_parser`/`get_repository` from `routes/articles.py` today — same cross-module pattern)
- `api/routes/public_review.py` → `ArticleCard`, `ReviewPageOut`, `ReviewArticleOut`, `ApproveRequest`, `RequestChangesRequest`, `ReviewActionOut`
- `api/routes/review_link.py` → `ReviewLinkOut`
- `api/routes/report.py` → `ChangeRoundsEntry`, `UpcomingEntry`, `PublishedEntry`, `NeedsAttentionEntry`, `ReportOut`

Nothing outside these 6 route files imports `app.api.schemas`: no test imports it directly, `scripts/export_openapi.py` only imports `app.api.main:app`, and the web app consumes the generated OpenAPI client, never this module. The split is fully contained to these 6 files plus the new package.

There's no existing precedent in this repo for turning one previously-flat file into a package — `core/domain/`, `adapters/`, etc. were all designed as directories from the start, and every `__init__.py` in the repo today is an empty marker. T-024 is the closest precedent: a flat file (`main.py`'s inline exception handling) outgrew one concern and was split into new single-purpose files, with `docs/architecture.md` updated in the same change.

### Design
New package `server/app/api/schemas/` replaces `schemas.py`:

| Module | Classes |
| --- | --- |
| `auth.py` | `SessionRequest` |
| `articles.py` | `EventOut`, `ArticleSummary`, `ArticleDetail`, `ArticlesOut`, `ScheduleRequest`, `ArticleUpdate` (keeps `_SLUG_RE` and both `field_validator`s: slug, tz-aware `publish_at`) |
| `imports.py` | `ArticlePaste`, `UploadFileResult`, `UploadResponse` (imports `ArticleSummary`, `ArticleDetail`, `EventOut` from `.articles`) |
| `public_review.py` | `ArticleCard`, `ReviewPageOut`, `ReviewArticleOut`, `ApproveRequest`, `RequestChangesRequest`, `ReviewActionOut` |
| `review_link.py` | `ReviewLinkOut` |
| `report.py` | `ChangeRoundsEntry`, `UpcomingEntry`, `PublishedEntry`, `NeedsAttentionEntry`, `ReportOut` |
| `__init__.py` | empty package marker |

Each of the 6 route files changes its import from `from app.api.schemas import (...)` to `from app.api.schemas.<module> import (...)` (`imports.py` gains a second import line from `.articles`). No re-export shim in `__init__.py` — every route imports directly from the submodule that owns the class, so it's always obvious where a schema lives.

### Decisions
- No `__init__.py` re-exports: keeps the ownership of each class obvious and matches T-024's approach of updating every caller's import path rather than leaving a compatibility shim behind.
- `schemas/report.py` intentionally reuses the "report" name alongside `core/domain/report.py` and `api/routes/report.py` — the same one-module-per-concern naming already used across layers (e.g. `core/use_cases/build_report.py` next to `core/domain/report.py`).
- `docs/architecture.md`'s folder-layout tree is updated in this same change (no prior convention existed for a package-ified file under `api/`).

## Acceptance criteria
- [x] `api/schemas.py` no longer exists; `api/schemas/` holds one module per route group above, plus an empty `__init__.py`.
- [x] Every response/request shape, field, and validator is byte-for-byte unchanged — the existing test suite passes with only import-path updates, no assertion changes.
- [x] All 6 route files import each class from the specific submodule that owns it, never from a package-level re-export.
- [x] `docs/architecture.md` folder layout shows `schemas/` and its files in place of the single `schemas.py` line.
- [x] Generated OpenAPI output (`web/lib/api/openapi.json`) is unchanged byte-for-byte after regenerating.

## Tasks
- [x] Create `api/schemas/__init__.py` (empty) and the six submodules (`auth.py`, `articles.py`, `imports.py`, `public_review.py`, `review_link.py`, `report.py`) with the class groupings above; delete `api/schemas.py`.
- [x] Update imports in `api/routes/auth.py`, `api/routes/articles.py`, `api/routes/imports.py`, `api/routes/public_review.py`, `api/routes/review_link.py`, `api/routes/report.py`.
- [x] `docs/architecture.md`: replace the `schemas.py` tree line with the `schemas/` directory and its files.
- [x] Run the full unit + integration suite, `uv run lint-imports`, and `uv run ruff check .` / `ruff format --check .` — must pass unmodified in assertions. (229 unit + 24 integration pass, run separately as `make test`/`make test-integration` do; running both marker sets in one pytest process surfaces 6 pre-existing failures from T-024's documented module-reload interaction, unrelated to this change and not how the project's own Makefile runs tests.)
- [x] `make gen-api` then diff `web/lib/api/openapi.json` against its current committed version to confirm it's unchanged; `pnpm typecheck`. (Diffed byte-for-byte identical before/after regenerating.)

## Out of scope
- Any change to a field name, type, default, or description on any schema — this is purely a file-layout move.
- Splitting any other flat `api/` file (`routes/*.py`, `auth.py`, `tags.py`) — schemas only.
