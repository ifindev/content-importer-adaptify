# T-033 UI revamp: every screen on fixtures

**Phase:** 4 · Frontend · **Status:** analyzed · **Size:** L
**Refs:** spec: Screens, Agency journey, Client journey, Article lifecycle; design canvas: [claude.ai artifact](https://claude.ai/artifact/QCpMywgpasGi231uuWrAMn), offline copy `design/canvas.html` (re-export with `python3 design/export.py`)
**Depends on:** T-026 (auth plumbing, proxy, shadcn components)

## Goal
Every screen on the design canvas is built in `web/` at its real route, in every state, on typed fixtures instead of API calls, and a Playwright suite proves each one renders, works by keyboard, and has no horizontal scroll at 375, 768 and 1280px. The wiring tickets (T-032, T-028, T-029) then only swap fixtures for the data layer.

## Analysis

### Screens and routes
The canvas is the source of truth for layout and styling. One canvas frame can cover several states; states without a frame follow the closest designed pattern.

| Canvas frame(s) | Route | Module |
| --- | --- | --- |
| Login | `/login` | `auth` |
| Site switcher (open) | shell, every agency route | `sites` |
| All sites, Add site (dialog), Zero sites | `/sites` (Add site opens as a dialog; `/sites?add=1` opens it directly, used by the switcher) | `sites` |
| Import | `/sites/[siteId]/import` | `articles` |
| Articles (desktop, mobile) | `/sites/[siteId]/articles` | `articles` |
| Article detail (desktop, mobile) | `/sites/[siteId]/articles/[id]` | `articles` |
| Report | `/sites/[siteId]/report` | `report` |
| Review page (mobile) | `/review/[token]` | `review` |
| Article reader, Request changes (mobile and desktop), Article review desktop | `/review/[token]/articles/[id]` | `review` |

- The `[siteId]` route segment lands here, not in T-032: `app/sites/[siteId]/...` replaces `/import`, `/articles`, `/report`. `proxy.ts` matches `/sites/:path*`; `/` goes to `/sites/{first site}/articles`, or `/sites` when there are none.
- Client review at `lg`+ is the 3-column layout (list | reader | decision panel). Below `lg` the review page and the reader are separate screens, as on the mobile frames.

### Fixture seam
- Each module gets `modules/<m>/data.ts`, the only import pages use for data. In this ticket it re-exports from `modules/<m>/fixtures/`.
- Fixture functions use **the exact names and signatures T-027 defines** (`listArticles(siteId, status?)`, `getArticle(siteId, id)`, `getReport(siteId)`, `getReview(token)`, `approve(token, id, …)`, …). Wiring a module becomes a one-line change in `data.ts`, and the fixtures folder is deleted.
- Fixture data is typed with `lib/api/schema.ts`, so typecheck catches a screen expecting a field the API doesn't send.
- Fixture mutations are Server Actions returning `MutationResult` after a short delay, so pending, success and error states are real UI, not mockups.
- **Scenarios:** fixture functions read a `fixture_scenario` cookie (`empty`, `wordpress-down`, `error:<code>`, …) to return each state. Playwright sets the cookie per test. The cookie and the scenarios disappear with the fixtures during wiring.

### Shared pieces
- **Tokens** in `app/globals.css`: border `oklch(0.93 0.006 264)`; the seven status colors as CSS variables used by `StatusBadge`; app background and inset panel. Text uses `--foreground`. Primary blue only on the one primary action per screen.
- **Shell** (restyle of T-026's): inset layout, raised active nav item, site switcher, "All sites" pinned at the bottom, user row with icon logout. Same breakpoints as T-026.
- **`ArticleEditor`**: Tiptap (`@tiptap/react`, StarterKit, Link, Table), moved here from T-028. Tiptap simple-editor layout: toolbar (undo/redo, text style menu, lists, bold, italic, link) plus a bubble menu on selection. Only marks the server's nh3 list keeps: h2–h4, p, ul/ol/li, a, strong, em, table. `editable=false` for read-only. Used by Import (paste) and Detail.
- `StatusBadge`, `SyncWarningBadge`, `WordPressBanner` (T-026) restyled to the canvas.

### States to build
| Screen | States |
| --- | --- |
| Login | Default, submitting, wrong credentials, too many attempts, network error, session expired (T-026's table) |
| Shell / switcher | Closed, open with search, site with failed connection (red dot), one site only |
| Sites | List, zero sites, Add site: default, submitting, `wp_connection_failed` inline, test connection pending / passed / failed |
| Import | Paste and Upload tabs, empty, uploading, results (clean, warnings, unreadable file), errors (`empty_content`, `payload_too_large`, `no_files`, `too_many_files`) |
| Articles | Loading skeleton, populated, no articles (Import button), no match for filter, WordPress banner, row pending (Set date, Retry), status filter with counts |
| Detail | Per status: Draft and Changes requested editable; Awaiting approval read-only with Pull back; Approved and Scheduled with "Editing resets the client's approval" confirm; Failed with error and Retry; Published read-only with live link. Plus saving, unsaved changes on leave (`beforeunload`), not found |
| Report | 3 summary cards, Articles by status, Needs attention, Change rounds (R6.4), Upcoming, Published, empty per list, approval speed "—", WordPress banner |
| Review page | Three groups, group empty, all empty, invalid token (404), rate limited |
| Reader | Awaiting approval with decision panel, read-only (upcoming, published), Request changes form, name remembered (`localStorage`, wrapped in try/catch), submitting, `article_changed`, `not_awaiting_approval` |

### Playwright UI suite
- `@playwright/test` in `web/` (moved here from T-029), Chromium, `webServer: pnpm dev`. Runs on fixtures alone: no API, emulators or WordPress needed.
- `web/e2e/ui/<screen>.spec.ts`, run at three viewport projects: 375, 768, 1280.
- Per screen and scenario: key content renders; `scrollWidth <= innerWidth`; Tab reaches the primary action; dialogs trap focus and close on Escape.
- `toHaveScreenshot` baselines, committed after a visual check against the canvas, catch later regressions.
- `make e2e-ui` runs it. T-029's full-flow test reuses this config under `web/e2e/flow/`.

### Open questions
- R6.4 asks for change rounds **per article**; the Report frame shows only the average. **Default:** add a "Change rounds" list (title + rounds, linked) styled like Upcoming.
- `/review/[token]` at `lg`+ with nothing selected has no frame. **Default:** list plus a reader placeholder ("Choose an article to read"); when exactly one article is waiting, open it.
- The Test connection button and the Sites list's connection status and counts have no API yet (see T-031's design follow-ups). **Default:** build them on a small fixture-only extension of the generated site type in `modules/sites/fixtures/`, the only exception to "API types are generated". It goes away when a follow-up API ticket adds the fields, or the UI drops them.

### Decisions
Update these docs as part of this ticket:
- **workflow.md, plan README:** Phase 4 builds every screen's UI on fixtures first, then the data layer, then wiring.
- **architecture.md Frontend:** `data.ts` fixture seam and scenario cookie; Tiptap editor; design tokens; route structure under `/sites/[siteId]`. **Testing:** the Playwright UI suite.
- **spec.md Screens:**
  - Add the Sites screen and site switcher (with T-031's scope change).
  - Client review at desktop width is one 3-column page.
  - Request changes is an inline form: bottom sheet on mobile, side panel on desktop.
  - The client's name is an inline field, remembered on the device.
- **Status filter** is a select at every width ("All", with per-status counts in the options), not tabs at `md`+ (changes T-028's earlier analysis).
- **Report layout:** summary cards (published this month, time to approval, change rounds) plus an "Articles by status" list, instead of one stat card per status.

## Acceptance criteria
- [ ] Every frame on the canvas exists at its route and matches the design at 1280px (and 390px for mobile frames).
- [ ] Every state in the table renders, selectable with the `fixture_scenario` cookie.
- [ ] No page imports fixtures directly; every data read and mutation goes through `modules/<m>/data.ts` with T-027's signatures.
- [ ] `pnpm typecheck` passes with fixtures typed from `lib/api/schema.ts` (the sites extension aside).
- [ ] `make e2e-ui` passes at 375, 768 and 1280px: content, no horizontal scroll, keyboard reach, screenshot baselines.
- [ ] Old `/import`, `/articles`, `/report` routes removed; proxy guards `/sites/:path*`.
- [ ] Docs updated per Decisions.

## Tasks
- [ ] Tokens in `globals.css`; restyle `StatusBadge`, `SyncWarningBadge`, `WordPressBanner`.
- [ ] Route restructure to `app/sites/[siteId]/...`; update `proxy.ts` and its tests.
- [ ] Shell restyle with site switcher and "All sites".
- [ ] `modules/<m>/data.ts` and `fixtures/` for sites, articles, report, review, with scenarios.
- [ ] `pnpm add @tiptap/react @tiptap/pm @tiptap/starter-kit @tiptap/extension-link @tiptap/extension-table` (+ row/cell/header if separate); `ArticleEditor`.
- [ ] Login restyle.
- [ ] Sites: list, zero-sites state, Add site dialog, switcher menu.
- [ ] Import, Articles, Detail, Report.
- [ ] Review page, reader, decision panel, request-changes form (sheet and side panel), desktop 3-column layout.
- [ ] Playwright setup, `web/e2e/ui/` specs, baselines, `make e2e-ui`.
- [ ] Docs: workflow.md, plan README, architecture.md, spec.md.

## Out of scope
- Any API call or real mutation (T-032, T-028, T-029 wire them through T-027).
- "Draft this change" (Phase 7). The canvas shows it; it's not rendered until then.
- Site removal/archive; client accounts.
