# T-034 Delete draft articles

**Phase:** 4 · API · **Status:** done · **Size:** S
**Refs:** R2.5, spec: Article lifecycle, API endpoints
**Depends on:** T-031

## Goal
The agency can delete an article that is still in Draft or Changes requested, one at a time or several at once, so duplicate or abandoned imports don't clutter the articles list.

## Analysis

### API
`DELETE /sites/{siteId}/articles/{id}`

| Case | Status | Body |
| --- | --- | --- |
| Draft or Changes requested | 204 | — |
| Any other status | 409 | `{"code": "not_deletable"}` |
| Unknown article | 404 | `{"code": "not_found"}` |
| Unknown site | 404 | `{"code": "site_not_found"}` |

No bulk endpoint: the UI's "Delete selected" calls this once per article and reports the ones that failed.

### Data changes
- Hard delete: the article document and its events subcollection are removed (Firestore `recursive_delete`).

### Core
- New use case `delete_article`: loads the article, raises `NotDeletableError` unless the status is Draft or Changes requested, then calls a new `ArticleRepository.delete_article(article_id)`.
- Map `NotDeletableError` to `409 not_deletable` in `error_handlers.py`.
- No WordPress call: a deletable article has never been sent to WordPress.

### Edge cases
| Case | Behavior |
| --- | --- |
| Article sent for review while the agency had the list open | 409 `not_deletable`; the UI shows the message and refreshes. |
| Changes requested article | Deleted. It also disappears from the client's review page, which only lists Awaiting approval, Approved, Scheduled and Published. |
| Report | Counts and change rounds no longer include it. |

### Decisions
- Hard delete, not archive: only pre-WordPress articles qualify, so there is nothing in WordPress to clean up and nothing to restore.
- Awaiting approval can't be deleted; the agency pulls it back first.

## Acceptance criteria
- [x] `DELETE` returns 204 for Draft and Changes requested, and the article and its events are gone.
- [x] Every other status returns `409 not_deletable` and changes nothing.
- [x] Unknown article and unknown site return 404.
- [x] Unit tests cover the status × delete table; the Firestore adapter test covers removing the events.
- [x] `openapi.json` and `web/lib/api/schema.ts` regenerated.

## Tasks
- [x] `NotDeletableError`, `delete_article` use case, unit tests (status table).
- [x] `ArticleRepository.delete_article` in the port, in-memory and Firestore adapters.
- [x] Route and error mapping.
- [x] `make gen-api`.

## Out of scope
- Deleting Approved, Scheduled, Failed or Published articles (they may exist in WordPress).
- Undo or restore.
- The UI: T-033 builds it on fixtures (`deleteArticle(siteId, id)`), T-028 wires it.
