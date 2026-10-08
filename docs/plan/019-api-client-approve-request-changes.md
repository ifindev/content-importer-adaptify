# T-019 Client approve and request changes

**Phase:** 3 · API · **Status:** done · **Size:** M
**Refs:** R3.4, R3.5, spec: Approval rules, API endpoints (Client) Decisions
**Depends on:** T-018

## Goal
The client approves an article or requests changes with a comment, typing their name once — this is the core approval rule the whole product exists to enforce: the client must approve the exact text that goes live.

## Analysis

### Flow
1. `POST /review/{token}/articles/{id}/approve`: body `{client_name, version}`. Token resolves the site; article must be `AwaitingApproval`. If `version` doesn't match the article's current `version`, refuse with 409 `article_changed` (spec's decision — stops a stale tab approving text the client never saw). On match: `AwaitingApproval → Approved`, `approved_version = version`, append `approved` event with `actor = client_name`.
2. `POST /review/{token}/articles/{id}/request-changes`: body `{client_name, comment, version}`. Same token/status/version checks. On match: `AwaitingApproval → ChangesRequested`, store `comment` on the article (surfaced to the agency per R3.5), append `changes_requested` event with `actor = client_name`, `data: {comment}`.

### API
`POST /review/{token}/articles/{id}/approve`

| Field | Type | Rules |
| --- | --- | --- |
| `client_name` | string | required, 1–100 chars |
| `version` | int | required, must equal the article's current `version` |

| Case | Status | Body |
| --- | --- | --- |
| OK | 200 | `{id, status}` |
| Version mismatch | 409 | `{code: "article_changed"}` |
| Not Awaiting approval | 409 | `{code: "not_awaiting_approval"}` |
| Unknown token or article | 404 | `{code: "not_found"}` |

`POST /review/{token}/articles/{id}/request-changes`

| Field | Type | Rules |
| --- | --- | --- |
| `client_name` | string | required, 1–100 chars |
| `comment` | string | required, 1–2000 chars |
| `version` | int | required, must match current |

Same status codes as approve, plus the comment is stored.

### Data changes
`Article` needs a `client_comment: str | None` field (not explicitly listed in spec's Data model table, which only shows it living on the article conceptually via R3.5 — **gap found here**; add it to `spec.md`'s Data model as part of this ticket). Cleared when the article is next edited or resubmitted (so a stale comment doesn't linger after the agency addresses it) — cleared in T-015's edit use case and T-017's send-for-review use case; **follow-up:** confirm those two tickets clear it (if T-015/T-017 ship first, come back and add the clear there instead of duplicating logic here).

### Core
`core/use_cases/review.py`: add `approve(token, article_id, client_name, version)`, `request_changes(token, article_id, client_name, comment, version)`. Both: resolve site by token (reuse T-018's lookup), load article, check `version`, check status via `lifecycle.transition`, save.

### Edge cases
| Case | Behavior |
| --- | --- |
| Client approves, then immediately reloads and approves again | Second call: status is now `Approved`, not `AwaitingApproval` → 409 `not_awaiting_approval` |
| Two browser tabs, one approves then the other (same version) | First succeeds; second now sees status `Approved` → 409 `not_awaiting_approval` (the version check only matters when the agency changed the text in between — the status check alone covers the double-submit case) |
| Agency pulls back between client loading the page and clicking approve | `version` unchanged but status is `Draft` → 409 `not_awaiting_approval` takes precedence over the version check |
| `client_name` differs between approve attempts on a resubmission | No identity check across rounds — each event just records whoever typed the name that time (matches spec: "so the agency knows who decided", not an identity system) |

## Acceptance criteria
- [x] Approve with the current `version` moves `AwaitingApproval → Approved`, sets `approved_version`, logs the client's name.
- [x] Approve with a stale `version` returns 409 `article_changed` and changes nothing.
- [x] Request changes stores the comment, moves to `ChangesRequested`, logs the client's name and comment as an event.
- [x] Either action from a non-`AwaitingApproval` status returns 409 `not_awaiting_approval`.
- [x] `spec.md`'s Data model updated with `client_comment`.
- [x] Swagger updated (via `pnpm gen:api`). Postman is a manual, local step per `docs/workflow.md` (no collection file is committed to the repo) — left for the user to do themselves; not part of this implementation.

## Tasks
- [x] Add `client_comment` to `core/domain/models.py` and `spec.md`.
- [x] `core/use_cases/review.py`: `approve`, `request_changes`.
- [x] `api/routes/public_review.py`: both routes.
- [x] Unit tests: version match/mismatch, status table, event content.
- [x] Integration test: Firestore emulator, full approve round-trip.
- ~~Postman: chained request folder (paste → send-for-review → approve).~~ Dropped: the repo has no Postman collection; Swagger is the API reference (T-038).
- [x] `pnpm gen:api`.

## Follow-ups closed by this ticket
- `client_comment` is now cleared on edit (`edit_article.py`) and on resubmit (`send_for_review` in `review.py`), closing the gap the ticket originally flagged as a follow-up for T-015/T-017.

## Out of scope
- AI drafting of the requested change (T-0xx, Phase 7).
