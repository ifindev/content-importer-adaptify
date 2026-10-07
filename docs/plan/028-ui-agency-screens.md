# T-028 Agency screens

**Phase:** 4 · Frontend · **Status:** analyzed · **Size:** L
**Refs:** E1, E2, R3.2, R3.5–R3.7, E4, R5.1–R5.3, R6.1–R6.4, spec: Screens, Agency journey, Article lifecycle
**Depends on:** T-026, T-027, T-032 (every route below lives under `/sites/{siteId}/...`)

## Goal
The agency does its whole job in the browser: import, edit, send for review, handle changes, schedule, retry, and read the report, on any screen size.

## Analysis
Each screen starts with a `/design` pass covering the States and Elements below, then gets built on T-027. Every screen: mobile-first, no horizontal scroll at 375px, dates through `<LocalTime>`, errors through `messageFor`, success through a toast.

### Shared: `ArticleEditor`
- Tiptap (`@tiptap/react`, StarterKit, Link, Table) in `modules/articles/components/`. Used by Import and Detail.
- Extensions limited to what the server's nh3 list keeps: h2–h4, p, ul/ol/li, a, strong, em, table. The editor never produces something the server will strip.
- Toolbar: heading levels, bold, italic, lists, link, table. Wraps on mobile; sticky at the top of the editor on scroll.
- Outputs HTML (`editor.getHTML()`). `readOnly` prop for Awaiting approval and later statuses.

All routes below live under `/sites/[siteId]/...` (T-032); paths are written without the prefix for brevity.

### Import (`/import`)
| Element | Notes |
| --- | --- |
| Tabs: Paste / Upload | Full-width tabs on mobile |
| Paste: title, slug, editor, Save | Title optional on paste — server derives it (R1.5); slug optional |
| Upload: drop zone | Native `<input type=file multiple accept=".docx">` behind a label styled as a drop zone; drag-and-drop via `onDrop` |
| Results list | One row per file: ✓ title + warnings + "Open", or ✗ filename + message |

| State | UI |
| --- | --- |
| Empty | Placeholder text in editor / drop zone hint |
| Saving / uploading | Button disabled, spinner; upload shows file count |
| Paste saved | Redirect to `/articles/{id}`, toast "Article imported" |
| Upload done | Results list stays on screen |
| Warnings (R1.4) | Amber alert per article, e.g. "This document had 3 images. Images are not imported." |
| Errors | `empty_content`, `payload_too_large`, `no_files`, `too_many_files`, per-file codes |

### Articles (`/articles`)
| Element | Notes |
| --- | --- |
| Header: Copy review link, Reset link | Copy → clipboard + toast. Reset → confirm dialog "The old link stops working" (R3.7) |
| Status filter | URL param via `useFilterParams`. Tabs at `md`+, Select below |
| WordPress banner | When the list response flags WordPress unreachable (R5.3) |
| Table (`md`+) / cards (< `md`) | Title (link to detail), status badge, sync warning badge, publish field, live URL |
| Publish field | Approved: `datetime-local` + Schedule. Scheduled: same, prefilled, Save = date change (R4.5). Failed: `last_error` + Retry. Published: date + live link. Else: — |

| State | UI |
| --- | --- |
| Loading | Skeleton rows / cards |
| No articles at all | Empty state with "Import articles" button |
| None for this filter | "No articles with this status" + clear filter |
| Scheduling | Row button disabled with spinner |
| Errors | `not_schedulable`, `publish_at_in_past`, `wordpress_error` (row goes Failed after revalidate), `not_failed` |

### Article detail (`/articles/{id}`)
| Element | Notes |
| --- | --- |
| Header | Title, status badge, sync warning badge, `last_error` alert if Failed |
| Form | Title, slug, `ArticleEditor`, Save |
| Actions by status | Draft / Changes requested: Save, Send for review. Awaiting approval: read-only + Pull back (R3.6). Approved / Scheduled: Edit → confirm "Editing resets the client's approval" (R2.3) → editable. Failed: Retry. Published: read-only + live link |
| Side panel | Client comment (R3.5, highlighted when Changes requested), history log: event, actor, time (R2.4) |

Layout: two columns at `lg` (editor | side panel). Below `lg`, side panel goes under the editor; history collapses to the last 5 with "Show all".

| State | UI |
| --- | --- |
| Not found | `notFound()` → agency 404 |
| Saving | Disabled form, spinner |
| Unsaved changes + navigate away | `beforeunload` prompt |
| Errors | `not_editable`, `empty_update`, `empty_content`, `not_sendable`, `not_awaiting_approval`, `wordpress_error` |

### Report (`/report`)
| Block | UI |
| --- | --- |
| Status counts + published this month | Stat cards: 1 col mobile, 2 at `sm`, 4 at `lg` |
| Approval speed | Humanized ("2 days 4 h"); "—" when null |
| Change rounds | List: title + rounds, linked |
| Upcoming | Title + `<LocalTime>`, soonest first |
| Published | Title + date + live link |
| Needs attention | Title + reason badge (Failed, Late, Changed, Missing) + detail, linked to the article |
| Banner | `wordpress_unreachable` → `WordPressBanner` |

Empty states per list ("Nothing scheduled", etc.). Lists are cards on mobile, tables at `md`+.

### Edge cases
| Case | Behavior |
| --- | --- |
| Client approves while the agency has the detail page open | Agency's next Save gets `not_editable`; message tells them to reload |
| Paste from Google Docs with styles | Tiptap drops unknown marks; server cleans again |
| Very long titles / URLs | Truncate with `title` attribute; URLs `break-all` in cards |

### Decisions
- One shared `ArticleEditor`; no second editor for read-only, just `editable=false`.
- Scheduling lives in the list (spec: "The articles table carries most of the daily work"), not on the detail page.

## Acceptance criteria
- [ ] Paste and multi-file upload create Drafts; warnings show (R1.1, R1.2, R1.4).
- [ ] Detail: edit only in Draft / Changes requested; Approved/Scheduled edit asks first, then resets to Draft (R2.2, R2.3); history and comment show (R2.4, R3.5).
- [ ] Send for review, pull back, schedule, date change, retry all work from the UI (R3.6, R4.1–R4.5).
- [ ] Copy and reset review link work (R3.2, R3.7).
- [ ] Sync warnings and the WordPress banner show (R5.1–R5.3).
- [ ] Report shows every block, with "—" for no approvals (R6.1–R6.4).
- [ ] Every error code listed above shows its message.
- [ ] All four screens: no horizontal scroll at 375, 768, 1280px; keyboard works (editor toolbar included).
- [ ] architecture.md Frontend updated (editor, responsive convention).

## Tasks
- [ ] `/design` for Import, Articles, Detail, Report.
- [ ] `pnpm add @tiptap/react @tiptap/pm @tiptap/starter-kit @tiptap/extension-link @tiptap/extension-table` (+ table row/cell/header if separate).
- [ ] `ArticleEditor`.
- [ ] Import page + components.
- [ ] Articles page: filter, table/cards, schedule/retry row actions, review link header.
- [ ] Detail page: form, status actions, confirm dialog, side panel.
- [ ] Report page.
- [ ] Docs.

## Out of scope
- "Draft this change" (Phase 7). Bulk actions. Image import.
