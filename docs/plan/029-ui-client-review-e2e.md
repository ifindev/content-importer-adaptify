# T-029 Client review: wiring and full-flow test

**Phase:** 4 · Frontend · **Status:** analyzed · **Size:** M
**Refs:** R3.3–R3.5, R6.5, R8.2, spec: Client journey, Client view; plan: Phase 4 "done when"
**Depends on:** T-027, T-028, T-032 (the agency must create/select a site before importing), T-033 (review screens on fixtures, Playwright setup)

## Goal
The review page and reader T-033 built on fixtures run on real data through the review token, without an account. One Playwright test then proves the whole flow works in the browser, agency and client, which closes Phase 4.

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

### Full-flow test
Uses T-033's Playwright config; the spec lives in `web/e2e/flow/full-flow.spec.ts`.
- `make e2e`: needs `make up`, `make wp-setup`, `make agency-user` done first.
1. Logged out, `/sites` → `/login`.
2. Log in with `AGENCY_EMAIL` / `AGENCY_PASSWORD`.
3. Create a site through Add Site against the local WordPress container; land on `/sites/{siteId}/articles`.
4. Paste an article with a unique title; send for review; read the review link.
5. New browser context (no cookies): open the link, check there's no sidebar, open the article, approve as "Sam".
6. Agency: schedule it one minute ahead; wait; run `make wp-cron` through a test helper (`execSync`); reload `/sites/{siteId}/articles`; see Published with a live URL.
7. Access: `/review/not-a-token` shows the 404 page.

### Edge cases
| Case | Behavior |
| --- | --- |
| Client double-taps Approve | Button disabled while pending (T-033) |
| Agency pulls the article back while the client reads | Decision gets `not_awaiting_approval` or `article_changed`; message shown |

## Acceptance criteria
- [ ] The review page shows the three groups from real data, with dates and live links (R3.3, R6.5).
- [ ] Approve and request changes work; the comment appears on the agency detail page (R3.4, R3.5).
- [ ] `article_changed` and `not_awaiting_approval` show their messages.
- [ ] Works without any login (R8.2).
- [ ] No fixtures left in `modules/review`; T-033's UI suite still passes.
- [ ] `make e2e` passes on a fresh `make up`.
- [ ] Phase 4 marked done in `docs/plan/README.md`.

## Tasks
- [ ] Point `modules/review/data.ts` at T-027's repository; delete the review fixtures.
- [ ] Full-flow spec, test helper for `make wp-cron`, `make e2e`.
- [ ] Docs: architecture.md (reader HTML decision; Testing mentions the full-flow test).

## Out of scope
- UI, layout and states (T-033).
- Client accounts, inline comments, passcodes (spec: Out of scope).
- Cross-browser e2e matrix.
