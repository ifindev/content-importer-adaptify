# T-029 Client review screens and full-flow test

**Phase:** 4 · Frontend · **Status:** analyzed · **Size:** L
**Refs:** R3.3–R3.5, R6.5, R8.2, spec: Client journey, Client view; plan: Phase 4 "done when"
**Depends on:** T-026, T-027, T-028

## Goal
The client opens the link on a phone, reads each article, and approves or requests changes without an account. One Playwright test then proves the whole flow works in the browser, agency and client, which closes Phase 4.

## Analysis
Design with `/design` first, mobile-first (clients open links from email on a phone).

### Review page (`/review/{token}`)
| Element | Notes |
| --- | --- |
| Header | Site name (from `getReview`), set in T-026's review layout |
| Waiting for your review | Cards: title, "Read and decide" |
| Upcoming | Title + `<LocalTime>` publish date |
| Published | Title + date + live link (`target=_blank rel="noopener noreferrer"`) |

| State | UI |
| --- | --- |
| Loading | Skeleton cards |
| Group empty | One line: "Nothing waiting for you right now." etc. |
| All empty | "No articles yet." |
| Bad / reset token | T-026's generic 404 |
| `rate_limited` | T-026's error state |
| WordPress unreachable | **Not shown.** The client view hides internals (spec: Client view). Groups render from stored data |

### Reader (`/review/{token}/articles/{id}`)
| Element | Notes |
| --- | --- |
| Back link | To the review page |
| Article | Title + body with prose styles (`@tailwindcss/typography` or hand-written styles for h2–h4, lists, tables, links) |
| Action bar | Approve, Request changes. Sticky at the bottom on mobile, inline at `md`+. 44px min tap targets |
| Name prompt | Dialog on first decision; stored in `localStorage` (`client_name`), read/write wrapped in try/catch. Prefilled on later decisions, editable |
| Request changes | Dialog with name + comment (required) |
| After decision | Toast + redirect to the review page; the article moves groups |

Only Awaiting approval articles show the action bar. Upcoming and published articles open read-only.

| Code | Message |
| --- | --- |
| `article_changed` | "This article was updated since you opened it. Reload to read the latest version." + Reload button |
| `not_awaiting_approval` | "A decision was already made on this article." |
| `not_found` | 404 page |
| `rate_limited` | "Too many requests. Try again in a minute." |

### Decisions
- The body is rendered with `dangerouslySetInnerHTML`. The server already cleans it with nh3 to the allowed tags at import and on every edit, so there is no second sanitizer in the browser. Record in architecture.md.
- The banner is hidden on client pages.

### Full-flow test
- `@playwright/test` in `web/`, `playwright.config.ts` with `baseURL=http://localhost:3000`, Chromium only.
- `make e2e`: needs `make up`, `make wp-setup`, `make agency-user` done first; runs `pnpm exec playwright test`.
- One spec, `e2e/full-flow.spec.ts`:
  1. Logged out, `/articles` → `/login`.
  2. Log in with `AGENCY_EMAIL` / `AGENCY_PASSWORD`.
  3. Paste an article with a unique title; send for review; read the review link.
  4. New browser context (no cookies): open the link, check there's no sidebar, open the article, approve as "Sam".
  5. Agency: schedule it one minute ahead; wait; run `make wp-cron` through a test helper (`execSync`); reload `/articles`; see Published with a live URL.
  6. Access: `/review/not-a-token` shows the 404 page.
  7. Responsive: at 375px, every screen visited has `scrollWidth <= innerWidth`.

### Edge cases
| Case | Behavior |
| --- | --- |
| `localStorage` blocked (private mode) | Name asked each time; nothing breaks |
| Client double-taps Approve | Button disabled while pending |
| Agency pulls the article back while the client reads | Decision gets `not_awaiting_approval` or `article_changed`; message shown |

## Acceptance criteria
- [ ] The review page shows the three groups with dates and live links (R3.3, R6.5).
- [ ] Approve and request changes work, with the name asked once and remembered (R3.4); the comment appears on the agency detail page (R3.5).
- [ ] `article_changed` and `not_awaiting_approval` show their messages.
- [ ] Works without any login (R8.2); no agency UI on client pages.
- [ ] Usable at 375px with the sticky action bar; no horizontal scroll at 375, 768, 1280px.
- [ ] `make e2e` passes on a fresh `make up`.
- [ ] Phase 4 marked done in `docs/plan/README.md`.

## Tasks
- [ ] `/design` for the review page and reader.
- [ ] `ReviewPage`, `ReviewArticlePage`, decision dialogs, action bar.
- [ ] Prose styles for the reader.
- [ ] Playwright setup, spec, `make e2e`.
- [ ] Docs: architecture.md (reader HTML decision, Testing section mentions e2e).

## Out of scope
- Client accounts, inline comments, passcodes (spec: Out of scope).
- Cross-browser e2e matrix.
