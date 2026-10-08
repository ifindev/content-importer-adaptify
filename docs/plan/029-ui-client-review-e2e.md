# T-029 Client review: wiring and full-flow check

> **Re-scoped 2026-10-08:** T-027 already did the wiring (repositories, swapped seams, fixtures deleted). What's left here is the manual pass in the browser against `make up` for the flows and acceptance criteria below.

**Phase:** 4 · Frontend · **Status:** done · **Size:** M
**Refs:** R3.3–R3.5, R6.5, R8.2, spec: Client journey, Client view; plan: Phase 4 "done when"
**Depends on:** T-027, T-028, T-032 (the agency must create/select a site before importing), T-033 (review screens on fixtures)

## Goal
The review page and reader T-033 built on fixtures run on real data through the review token, without an account. A hand check of the whole flow in the browser, agency and client, then closes Phase 4. There is no automated end-to-end suite for the MVP.

## Analysis
All UI, states and layout are done in T-033. This ticket points `modules/review/data.ts` at T-027's repository, deletes the review fixtures, and adds the full-flow test.

### Wiring
| Screen | Reads | Mutations | After success |
| --- | --- | --- | --- |
| Review page | `getReview(token)` | — | — |
| Reader | `getReviewArticle(token, id)` (with `version`) | `approve(token, id, {client_name, version})`, `requestChanges(token, id, {client_name, comment, version})` | Toast + redirect to the review page; the article moves groups |

- The decision panel shows only for Awaiting approval articles, driven by the response.
- Live links open with `target=_blank rel="noopener noreferrer"`.

| Code | Message |
| --- | --- |
| `article_changed` | "This article was updated since you opened it. Reload to read the latest version." + Reload button |
| `not_awaiting_approval` | "A decision was already made on this article." |
| `not_found` | 404 page |
| `rate_limited` | "Too many requests. Try again in a minute." |

### Decisions
- The body is rendered with `dangerouslySetInnerHTML`. The server already cleans it with nh3 to the allowed tags at import and on every edit, so there is no second sanitizer in the browser. Record in architecture.md.
- The WordPress banner is hidden on client pages (spec: Client view).
- Below `lg`, "Request changes" opens a bottom sheet that behaves like a modal: the page behind it doesn't scroll. The sheet has rounded top corners (14px, like dialogs) and is capped at 80svh; the heading, name field and Cancel / Send request stay in view, and only the comment field scrolls (it isn't resizable there).

### Full-flow check (by hand)
Needs `make up`, `make wp-setup` and `make agency-user` first.
1. Logged out, `/sites` → `/login`.
2. Log in with `AGENCY_EMAIL` / `AGENCY_PASSWORD`.
3. Create a site through Add Site against the local WordPress container; land on `/sites/{siteId}/articles`.
4. Paste an article with a unique title; send for review; read the review link.
5. New browser context (no cookies): open the link, check there's no sidebar, open the article, approve as "Sam".
6. Agency: schedule it one minute ahead; wait; run `make wp-cron`; reload `/sites/{siteId}/articles`; see Published with a live URL.
7. Access: `/review/not-a-token` shows the 404 page.

### Edge cases
| Case | Behavior |
| --- | --- |
| Client double-taps Approve | Button disabled while pending (T-033) |
| Agency pulls the article back while the client reads | Decision gets `not_awaiting_approval` or `article_changed`; message shown |

## Acceptance criteria
- [x] The review page shows the three groups from real data, with dates and live links (R3.3, R6.5).
- [x] Approve and request changes work; the comment appears on the agency detail page (R3.4, R3.5).
- [x] `article_changed` and `not_awaiting_approval` show their messages.
- [x] Works without any login (R8.2).
- [x] No fixtures left in `modules/review`; `pnpm typecheck` passes.
- [x] The full-flow check above passes on a fresh `make up`.
- [x] Phase 4 marked done in `docs/plan/README.md`.

## Tasks
- [x] Point `modules/review/data.ts` at T-027's repository; delete the review fixtures (done in T-027).
- [x] Full-flow check by hand (steps above).
- [x] Docs: architecture.md reader HTML decision (already recorded). ~~Full-flow test~~: out of scope.

## Fixed after the wiring audit (2026-10-08)
Code is done; the boxes above are ticked during the browser pass.
- After Approve or Request changes the client goes back to the review page. Before, the reader reloaded an article the client can no longer see and showed "This link isn't valid".
- The WordPress banner no longer shows on client pages.
- Rate limiting shows its own screen in production too: a 429 is returned as data, not thrown (Next hides thrown messages).
- Live links use `rel="noopener noreferrer"`.
- Waiting articles show the date they were sent (T-036).
- Removed copy for an "approved, no date yet" state the client never sees.

## Fixed during the browser pass (2026-10-08)
- The reader no longer scrolls the whole page at `lg`+: the shell is pinned to the viewport, and the article list, the article and the decision panel scroll on their own. Below `lg` the document scrolls as before, for the sticky decision bar.
- The review pages refetch on tab focus and from a Refresh button in the header (`RefreshOnFocus`), so an article the agency sends shows without a reload. A half-typed comment survives it.
- Mobile "Request changes" sheet: the page behind no longer scrolls, and a long comment scrolls inside the field instead of pushing the name and buttons out of the sheet (see Decisions).

## Out of scope
- UI, layout and states (T-033).
- Client accounts, inline comments, passcodes (spec: Out of scope).
- Any automated end-to-end suite (Playwright or similar), and a cross-browser matrix.
