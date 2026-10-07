# T-017 Send for review and pull back

**Phase:** 3 · API · **Status:** done · **Size:** S
**Refs:** R3.6, spec: Article lifecycle, API endpoints (Agency)
**Depends on:** T-013, T-015

## Goal
The agency moves an article from Draft or Changes requested onto the review page, or pulls one back to Draft before the client sees it.

## Analysis

### Flow
1. `POST /articles/{id}/send-for-review`: `Draft → AwaitingApproval` or `ChangesRequested → AwaitingApproval`. Appends a `sent_for_review` event — this is the timestamp T-022's report uses for approval-speed math (first `sent_for_review` to `approved`).
2. `POST /articles/{id}/pull-back`: `AwaitingApproval → Draft` only. Appends a `pulled_back` event.

### API
`POST /articles/{id}/send-for-review`

| Case | Status | Body |
| --- | --- | --- |
| From Draft or Changes requested | 200 | `ArticleDetail` |
| From any other status | 409 | `{code: "not_sendable"}` |

`POST /articles/{id}/pull-back`

| Case | Status | Body |
| --- | --- | --- |
| From Awaiting approval | 200 | `ArticleDetail` |
| From any other status | 409 | `{code: "not_awaiting_approval"}` |

Both 404 `not_found` if the article doesn't exist.

### Core
`core/use_cases/review.py` (shared file for all agency+client review actions per the folder layout — this ticket adds `send_for_review`, `pull_back`; T-019 adds `approve`, `request_changes` to the same file): both call `lifecycle.transition`, which already encodes the allowed pairs from T-013.

### Edge cases
| Case | Behavior |
| --- | --- |
| Send for review on first pass (Draft) vs. resubmission (Changes requested) | Same event type `sent_for_review` either way — the report ticket (T-022) distinguishes "first" vs. "resubmission" by counting events, not by a different event type |

## Acceptance criteria
- [x] Draft and Changes requested articles move to Awaiting approval; every other status is refused with 409.
- [x] Awaiting approval articles move back to Draft via pull-back; every other status is refused with 409.
- [x] Each transition appends the correct event type with an actor and timestamp.
- [x] Swagger updated (openapi.json regenerated). Postman: manual follow-up, re-import into Postman per `workflow.md` (see T-014's note).

## Tasks
- [x] `core/use_cases/review.py`: `send_for_review`, `pull_back` (appended to the file T-016 already created for `get_review_page`/`get_review_article`).
- [x] `api/routes/articles.py`: the two routes.
- [x] Unit tests: status × action table above.
- [x] Integration test: Firestore emulator round-trip.
- [x] `pnpm gen:api`.

## Out of scope
- The client's approve/request-changes actions (T-019).
- The review page listing (T-018).
