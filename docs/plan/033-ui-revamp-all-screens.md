# T-033 UI revamp: every screen on fixtures

**Phase:** 4 · Frontend · **Status:** in progress · **Size:** L
**Refs:** spec: Screens, Agency journey, Client journey, Article lifecycle; design canvas: [claude.ai artifact](https://claude.ai/artifact/QCpMywgpasGi231uuWrAMn), offline copy `design/canvas.html` (re-export with `python3 design/export.py`)
**Depends on:** T-026 (auth plumbing, proxy, shadcn components)

## Goal
Every screen on the design canvas is built in `web/` at its real route, in every state, on typed fixtures instead of API calls. Each one is checked by hand in the browser: it renders, works by keyboard, and has no horizontal scroll at 375, 768 and 1280px. The wiring tickets (T-032, T-028, T-029) then only swap fixtures for the data layer.

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
- Each module gets `modules/<m>/data.ts` (reads) and `modules/<m>/actions.ts` (writes), the only imports pages and components use for data. In this ticket they re-export from `modules/<m>/fixtures/`. Writes get their own file because client components can't import a module that also pulls in `server-only` reads.
- Seed data shared by every module (so the report and review page reflect agency changes) lives in `lib/fixtures/store.ts`; the scenario cookie helper is `lib/fixtures/scenario.ts`. Both are deleted with the fixtures.
- Fixture functions use **the exact names and signatures T-027 defines** (`listArticles(siteId, status?)`, `getArticle(siteId, id)`, `getReport(siteId)`, `getReview(token)`, `approve(token, id, …)`, …). Wiring a module becomes a one-line change in `data.ts`, and the fixtures folder is deleted.
- Fixture data is typed with `lib/api/schema.ts`, so typecheck catches a screen expecting a field the API doesn't send.
- Fixture mutations are Server Actions returning `MutationResult` after a short delay, so pending, success and error states are real UI, not mockups.
- **Scenarios:** fixture functions read a `fixture_scenario` cookie to return each state: `empty`, `no-sites`, `one-site`, `wordpress-down`, `slow` (loading skeletons), `rate-limited`, and `error:<code>` (every mutation fails with that code). Set it in devtools to check a state. The cookie and the scenarios disappear with the fixtures during wiring.

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
| Import | Paste (with Title field) and Upload tabs, empty, uploading, results (clean, unreadable file) with Delete and the Articles banner, errors (`empty_content`, `payload_too_large`, `no_files`, `too_many_files`) |
| Articles | Loading skeleton, populated, no articles (Import button), no match for filter, WordPress banner, row pending (Set date, Retry), status filter with counts, bulk select and delete |
| Detail | Per status: Draft and Changes requested editable; Awaiting approval read-only with Pull back; Approved and Scheduled with "Editing resets the client's approval" confirm; Failed with error and Retry; Published read-only with live link. Plus saving, unsaved changes on leave (`beforeunload`), not found |
| Report | 3 summary cards, Articles by status, Needs attention, Change rounds (R6.4), Upcoming, Published, empty per list, approval speed "—", WordPress banner |
| Review page | Three groups, group empty, all empty, invalid token (404), rate limited |
| Reader | Awaiting approval with decision panel, read-only (upcoming, published), Request changes form, name remembered (`localStorage`, wrapped in try/catch), submitting, `article_changed`, `not_awaiting_approval` |

### Checks
Playwright and new vitest tests are out of scope (see CLAUDE.md). Each screen and scenario is checked by hand in the browser at 375, 768 and 1280px: key content renders, no horizontal scroll, Tab reaches the primary action, dialogs and sheets close on Escape, and the main flows work.

### Open questions
- R6.4 asks for change rounds **per article**; the Report frame shows only the average. **Default:** add a "Change rounds" list (title + rounds, linked) styled like Upcoming.
- `/review/[token]` at `lg`+ with nothing selected has no frame. **Default:** list plus a reader placeholder ("Choose an article to read"); when exactly one article is waiting, open it.
- The Test connection button and the Sites list's connection status and counts have no API yet (see T-031's design follow-ups). **Default:** build them on a small fixture-only extension of the generated site type in `modules/sites/fixtures/`, the only exception to "API types are generated". It goes away when a follow-up API ticket adds the fields, or the UI drops them.

### Decisions
Update these docs as part of this ticket:
- **workflow.md, plan README:** Phase 4 builds every screen's UI on fixtures first, then the data layer, then wiring.
- **architecture.md Frontend:** `data.ts` / `actions.ts` fixture seam and scenario cookie; Tiptap editor; design tokens; route structure under `/sites/[siteId]`.
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
- [ ] No page imports fixtures directly; every read goes through `modules/<m>/data.ts` and every mutation through `modules/<m>/actions.ts`, with T-027's signatures.
- [ ] `pnpm typecheck` passes with fixtures typed from `lib/api/schema.ts` (the sites extension aside).
- [ ] Checked by hand at 375, 768 and 1280px: content, no horizontal scroll, keyboard reach.
- [ ] Old `/import`, `/articles`, `/report` routes removed; proxy guards `/sites/:path*`.
- [ ] Docs updated per Decisions.

## Tasks
- [ ] Tokens in `globals.css`; restyle `StatusBadge`, `SyncWarningBadge`, `WordPressBanner`.
- [ ] Route restructure to `app/sites/[siteId]/...`; update `proxy.ts` and its tests.
- [ ] Shell restyle with site switcher and "All sites".
- [ ] `modules/<m>/data.ts` and `fixtures/` for sites, articles, report, review, with scenarios.
- [ ] `pnpm add @tiptap/react @tiptap/pm @tiptap/starter-kit @tiptap/extension-table` (Tiptap 3's StarterKit includes Link; `TableKit` covers row/cell/header); `ArticleEditor`.
- [ ] Login restyle.
- [ ] Sites: list, zero-sites state, Add site dialog, switcher menu.
- [ ] Import, Articles, Detail, Report.
- [ ] Review page, reader, decision panel, request-changes form (sheet and side panel), desktop 3-column layout.
- [ ] Hand check of every screen and scenario at 375, 768 and 1280px.
- [ ] Docs: workflow.md, plan README, architecture.md, spec.md.

### Added after review
- **Delete drafts** (spec R2.5, API in T-034): checkboxes on deletable rows of the Articles list with a sticky "n selected · Delete" bar (one call per article, failures reported), Delete on Article detail, and Delete on each upload result. Every delete asks for confirmation. Fixture: `deleteArticle(siteId, id)`, `409 not_deletable` outside Draft and Changes requested.
- **Paste title:** a Title field above the paste editor. The client sends it as a leading `<h1>`, which the server's first-heading rule (R1.5) turns into the title; empty means the first heading is used, as before.
- **Edit and delete sites** (API in T-035): a "More actions" menu per row on the Sites list with Edit (the Add site dialog in edit mode, `?edit=<siteId>`; an empty password keeps the stored one) and Delete (confirm by typing the site name). Fixtures: `updateSite(siteId, form)`, `deleteSite(siteId)`.
- **Import banner:** after an upload, "n articles were added as Drafts. See them in Articles →".

### Gaps found while building
The generated schema lacks a few fields the canvas shows. The screens leave them out rather than extend the types; each needs an API follow-up or a design change:
- Articles list: no **Live URL** column and no **error line** under a Failed title (`ArticleSummary` has no `published_url` or `last_error`). The detail page shows both.
- Articles list: the per-row "More actions" menu is not built (no actions defined for it).
- Import upload results: per-file **warnings** ("3 images dropped") aren't shown, since `UploadFileResult.article` is a summary without `warnings`. The detail page shows them.
- Review page and reader: "Sent Oct 7" is not shown (`ArticleCard` and `ReviewArticleOut` have no sent date).
- Sites list: no "Current" badge (`/sites` has no current site).
- Report "Change rounds" card: the API has no average, so the page shows total rounds ÷ total articles.

## Out of scope
- Playwright and new vitest tests (CLAUDE.md).
- Any API call or real mutation (T-032, T-028, T-029 wire them through T-027).
- "Draft this change" (Phase 7). The canvas shows it; it's not rendered until then.
- Site archive/restore; client accounts.
