# T-032 Site switcher and Add Site screen

**Phase:** 4 · Frontend · **Status:** todo · **Size:** M
**Refs:** spec: Screens, E8 Access
**Depends on:** T-026 (access shell — finishes single-site as-is; this ticket extends its nav), T-031 (API: sites collection, siteId-scoped routes)

## Goal
The agency can see every client site it manages, switch between them, and add a new one — all from the app shell T-026 ships. Every existing/planned agency screen (T-027's data layer, T-028's screens) reads its `siteId` from the route instead of assuming one site, because this ticket lands before both.

## Analysis

### Flow
1. On login, the shell (T-026) now also loads `GET /sites`. Zero sites → the shell shows an empty state with "Add your first client site" instead of the articles table.
2. One or more sites → a site switcher in the shell nav lists them by name; picking one navigates to `/sites/{siteId}/articles`. The current site stays visible in the URL, so two clients can be open in separate tabs.
3. "Add site" (from the switcher or the empty state) opens a form: name, WordPress base URL, WordPress app password. Submitting calls `POST /sites` (T-031). A failed WordPress connection test shows the error inline on the form (`wp_connection_failed` → "Couldn't connect to WordPress with these details — check the URL and app password."); success navigates straight into the new site's (empty) articles screen.

### Web
- `SiteSwitcher`: lives in the shell nav built by T-026; lists sites from a new `sites.queries.ts`; writes nowhere itself, just navigates.
- `AddSiteForm`: a screen or modal (design pass decides which) with the three fields above; `sites.mutations.ts` wraps `POST /sites` and returns `{ ok, code }` per the existing mutation convention, so `wp_connection_failed` renders as a field-level error, not a crash.
- Every agency screen's routes gain a `[siteId]` segment (`app/sites/[siteId]/articles/...`), and every call T-027's data layer makes includes it — T-027 is sequenced after this ticket specifically so it's written against this shape from the start, not retrofitted.
- Empty state (zero sites) replaces the articles table, not just an empty table — a brand-new agency shouldn't see "no articles" when the real gap is "no sites yet."

### States
| State | Shows |
| --- | --- |
| Zero sites | Empty state, "Add your first client site" |
| 1+ sites, none selected (fresh login) | Switcher defaults to the first site (or the last one used — local-only convenience, no server state) |
| Add Site: submitting | Form disabled, spinner on submit |
| Add Site: `wp_connection_failed` | Inline error on the form, fields stay filled in |
| Add Site: success | Navigates to the new site's articles screen |

### Edge cases
| Case | Behavior |
| --- | --- |
| Switching sites while mid-edit on an article | Out of scope to guard specially — same as any other navigation away today; no unsaved-changes prompt unless T-028 already has one for other navigations |
| Only one site exists | Switcher still shows (as a single-item list), no special-casing to hide it |

## Acceptance criteria
- [ ] A fresh agency login with zero sites sees the "add your first site" empty state, not an empty articles table.
- [ ] The site switcher lists every site from `GET /sites` and navigates to `/sites/{siteId}/articles` on selection.
- [ ] The Add Site form calls `POST /sites`, surfaces `wp_connection_failed` inline, and navigates into the new site on success.
- [ ] Responsive at 375/768/1280px, keyboard-usable, matching T-026's existing shell conventions.

## Tasks
- [ ] Design pass (`/design`) for the switcher placement and the Add Site form/modal.
- [ ] `sites.queries.ts`, `sites.mutations.ts` in the data layer, typed from the regenerated schema (T-031's `pnpm gen:api`).
- [ ] `SiteSwitcher` component in the shell nav.
- [ ] `AddSiteForm` screen/modal.
- [ ] Route restructure: `[siteId]` segment ahead of every agency screen.
- [ ] Empty-state screen for zero sites.
- [ ] Tests for: zero-sites empty state, switcher navigation, Add Site success + `wp_connection_failed` path.

## Out of scope
- Site removal/archive in the UI.
- Cross-site report view.
- Any per-user/per-client access control UI (R8.1 stands — single shared login).
