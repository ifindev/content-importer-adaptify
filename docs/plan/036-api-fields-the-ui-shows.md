# T-036 API: fields the UI shows

**Phase:** 4 · API · **Status:** done · **Size:** S
**Refs:** spec: Screens, API endpoints; T-033 "Gaps found while building"
**Depends on:** T-031
**Improves:** T-014, T-018, T-022

## Goal
The design canvas shows a few values the API didn't send, so the screens left them out (T-033's gap list). With these fields the articles list, the upload results, the client review page and the report match the design without computing anything in the browser.

## Analysis

### API
| Response | New field | Source |
| --- | --- | --- |
| `ArticleSummary` (articles list, upload results) | `published_url`, `last_error` | Already on the article |
| `UploadFileResult` | `warnings` | The created article's import warnings |
| `ArticleCard`, `ReviewArticleOut` | `sent_for_review_at` | New `Article.sent_for_review_at`, set by `send_for_review` |
| `ReportOut` | `avg_change_rounds` | Change requests per article, over every article; null with none |

Also: a request that fails schema validation returns `422 {"code": "validation_error", "fields": [...]}` instead of FastAPI's `{"detail": [...]}`, so the web app shows a message instead of "Something went wrong".

### Data changes
- `articles/{id}`: optional `sent_for_review_at`. Articles sent before this ticket have none; the UI then shows "Needs your decision" instead of a date.

### Web
- Articles list: Live URL column at `lg`+, the WordPress error under a Failed title.
- Upload results: the warnings per file.
- Review page and reader: "Sent Oct 7".
- Report: the Change rounds card uses `avg_change_rounds`.

## Acceptance criteria
- [x] Each field is in `openapi.json` and `web/lib/api/schema.ts`.
- [x] Unit tests: list fields, upload warnings, `sent_for_review_at` on send, `avg_change_rounds` (value and null), `validation_error`.
- [x] The screens above show the fields.

## Out of scope
- A sent date on articles sent before this ticket (no backfill).
