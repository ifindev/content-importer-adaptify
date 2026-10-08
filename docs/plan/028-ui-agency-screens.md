# T-028 Agency screens: wiring

> **Re-scoped 2026-10-08:** T-027 already did the wiring (repositories, swapped seams, fixtures deleted). What's left here is the manual pass in the browser against `make up` for the flows and acceptance criteria below.

**Phase:** 4 · Frontend · **Status:** done · **Size:** M
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
- [x] Paste and multi-file upload create Drafts; warnings show (R1.1, R1.2, R1.4).
- [x] Detail: edit only in Draft / Changes requested; Approved edit asks first, then resets to Draft; Scheduled is read-only until unscheduled (R2.2, R2.3, R4.3); history and client comment show (R2.4, R3.5).
- [x] Send for review, pull back, schedule, date change, unschedule, retry and a new date on Failed all work from the UI (R3.6, R4.1–R4.5).
- [x] Copy and reset review link work (R3.2, R3.7).
- [x] Sync warnings and the WordPress banner show from real data (R5.1–R5.3).
- [x] Report shows every block from `GET /report`, with "—" when there are no approvals (R6.1–R6.4).
- [x] Every error code listed shows its message.
- [x] No fixtures left in `modules/articles` or `modules/report`; `pnpm typecheck` passes.

## Tasks
- [x] Point `modules/articles/data.ts` and `modules/report/data.ts` at T-027's repository; delete their fixtures (done in T-027).
- [x] Status filter counts per the open question (counted from the unfiltered list in `ArticlesPage.tsx`).
- [x] Manual pass of each flow against `make up`.
- [x] Docs, if any behavior differs from T-033's.

## Fixed after the wiring audit (2026-10-08)
Code is done; the boxes above are ticked during the browser pass.
- `wordpress_error` (a 502) now shows its message inline, and the page revalidates so the row shows Failed with its error. Before, it fell through to the generic error page.
- "Reset review link" beside "Copy review link", with a confirm; the new link is copied.
- Paste shows "Article imported." before opening the article.
- The schedule dialog keeps the picked date after `publish_at_in_past` (`onSubmit` instead of a form `action`, which React resets).
- Scheduled rows get "Change date" inline (R4.5); each row has a "More actions" menu (Open, View live, Copy live link, Delete).
- Activity shows "Agency", "WordPress" or the client's name instead of a Firebase uid.
- The `not_editable` message says to reload; schema validation errors show a message (`validation_error`).
- Live URL column and the error line under Failed titles (T-036).

## Fixed during the browser pass (2026-10-08)
- Fresh data: Articles and Article detail refetch on tab focus and from a Refresh button (`RefreshOnFocus`), so a client's decision shows without a reload. Off while the detail has unsaved changes.
- Activity: each "requested changes" entry opens to show its comment. The "Client feedback" box keeps the client's line breaks.
- Unschedule trashes the WordPress post (it stayed as a Draft), and the schedule dialog has its own date and time picker where past days and earlier times are faint, disabled text, so nothing under 5 minutes away can be picked (T-039).
- "Edit anyway" now makes the body editable: `useEditor` reads `editable` once, so `ArticleEditor` calls `setEditable` on change (without an update event, which marked every article as "Unsaved changes" and hid Refresh). Focus lands in the title.

## Out of scope
- UI, layout and states (T-033).
- "Draft this change" (Phase 7). Bulk actions. Image import.
