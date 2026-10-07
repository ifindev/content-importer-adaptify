# T-028 Agency screens: wiring

**Phase:** 4 · Frontend · **Status:** analyzed · **Size:** M
**Refs:** E1, E2, R3.2, R3.5–R3.7, E4, R5.1–R5.3, R6.1–R6.4, spec: Agency journey, Article lifecycle
**Depends on:** T-027 (data layer), T-032 (sites wired, `siteId` routes live), T-033 (the screens, on fixtures)

## Goal
The four agency screens T-033 built on fixtures run on real data, so the agency does its whole job in the browser: import, edit, send for review, handle changes, schedule, retry, and read the report.

## Analysis
All UI, states and layout are done in T-033. This ticket points `modules/articles/data.ts` and `modules/report/data.ts` at T-027's repository functions, deletes their fixtures, and checks each flow end to end against the API.

### Wiring per screen
| Screen | Reads | Mutations | After success |
| --- | --- | --- | --- |
| Import | — | `pasteArticle`, `uploadArticles` | Paste: redirect to detail + toast "Article imported". Upload: results list from per-file results |
| Articles | `listArticles(siteId, status)`, `getReviewLink(siteId)` | `scheduleArticle` (set date, and date change on Scheduled, R4.5), `retryArticle`, `resetReviewLink` | Revalidate list; toast |
| Detail | `getArticle(siteId, id)` | `updateArticle` (Approved/Scheduled after T-033's confirm, R2.3), `sendForReview`, `pullBack`, `retryArticle` | Revalidate detail and list; toast |
| Report | `getReport(siteId)` | — | — |

- Every `{ ok: false, code }` shows `messageFor(code)` in the place T-033 built for it. Codes: `empty_content`, `payload_too_large`, `no_files`, `too_many_files`, per-file upload codes, `not_editable`, `empty_update`, `not_sendable`, `not_awaiting_approval`, `not_schedulable`, `publish_at_in_past`, `wordpress_error`, `not_failed`.
- `not_found` on detail → `notFound()`.
- WordPress banner shows when the list or report response flags WordPress unreachable (R5.3).

### Open questions
- Where the status filter's per-status counts come from. **Default:** count from the unfiltered `listArticles(siteId)` response and filter in the page; an MVP site has at most a few hundred articles (spec: Data model decision).

### Edge cases
| Case | Behavior |
| --- | --- |
| Client approves while the agency has the detail page open | Next Save gets `not_editable`; the message tells them to reload |
| `wordpress_error` on schedule | Row goes Failed after revalidate, with `last_error` |
| Paste from Google Docs with styles | Tiptap drops unknown marks; the server cleans again |

### Decisions
- Scheduling lives in the list (spec: "The articles table carries most of the daily work"), not on the detail page.

## Acceptance criteria
- [ ] Paste and multi-file upload create Drafts; warnings show (R1.1, R1.2, R1.4).
- [ ] Detail: edit only in Draft / Changes requested; Approved/Scheduled edit asks first, then resets to Draft (R2.2, R2.3); history and client comment show (R2.4, R3.5).
- [ ] Send for review, pull back, schedule, date change and retry all work from the UI (R3.6, R4.1–R4.5).
- [ ] Copy and reset review link work (R3.2, R3.7).
- [ ] Sync warnings and the WordPress banner show from real data (R5.1–R5.3).
- [ ] Report shows every block from `GET /report`, with "—" when there are no approvals (R6.1–R6.4).
- [ ] Every error code listed shows its message.
- [ ] No fixtures left in `modules/articles` or `modules/report`; T-033's UI suite still passes.

## Tasks
- [ ] Point `modules/articles/data.ts` and `modules/report/data.ts` at T-027's repository; delete their fixtures.
- [ ] Status filter counts per the open question.
- [ ] Manual pass of each flow against `make up`.
- [ ] Docs, if any behavior differs from T-033's.

## Out of scope
- UI, layout and states (T-033).
- "Draft this change" (Phase 7). Bulk actions. Image import.
