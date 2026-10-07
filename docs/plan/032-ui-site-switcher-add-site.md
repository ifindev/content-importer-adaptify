# T-032 Sites: wiring for the switcher, sites list and Add Site

**Phase:** 4 · Frontend · **Status:** analyzed · **Size:** S
**Refs:** spec: Screens, E8 Access
**Depends on:** T-031 (API: sites collection, `siteId`-scoped routes), T-027 (`listSites`, `createSite`), T-033 (sites screens, switcher and `[siteId]` routes on fixtures)

## Goal
The agency sees every client site it manages, switches between them, and adds a new one, all on real data. T-033 built the screens and the `/sites/[siteId]/...` routes; this ticket points them at `GET /sites` and `POST /sites`.

## Analysis

### Flow
1. On login, the shell loads `listSites()`. Zero sites → `/sites` shows the "Add your first client site" empty state instead of an articles table.
2. One or more sites → the switcher lists them; picking one navigates to `/sites/{siteId}/articles`. The current site stays in the URL, so two clients can be open in separate tabs.
3. Add Site calls `createSite(form)`. `wp_connection_failed` → the inline error T-033 built ("Couldn't connect to WordPress with these details — check the URL and app password."), fields stay filled. Success → the new site's (empty) articles screen.
4. Test connection, connection status and site counts need a follow-up API ticket (see T-031's design follow-ups). Until it exists, those parts stay hidden and the connection test runs only on submit.

### States
| State | Shows |
| --- | --- |
| 1+ sites, none selected (fresh login) | First site, or the last used one (`localStorage`, local-only convenience) |
| Add Site: success | Navigates to the new site's articles screen |
| Unknown `siteId` in the URL | API `site_not_found` → agency 404 |

### Edge cases
| Case | Behavior |
| --- | --- |
| Switching sites mid-edit on an article | Same as any other navigation away; T-033's `beforeunload` prompt applies |
| Only one site exists | Switcher still shows it as a one-item list |

## Acceptance criteria
- [ ] A fresh agency login with zero sites lands on the empty state, not an empty articles table.
- [ ] The switcher and the sites list show every site from `GET /sites`; selecting one navigates to `/sites/{siteId}/articles`.
- [ ] Add Site calls `POST /sites`, shows `wp_connection_failed` inline, and navigates into the new site on success.
- [ ] Sites data uses only types from `lib/api/schema.ts`; the fixture-only extension is gone or limited to the hidden follow-up parts.
- [ ] No fixtures left in `modules/sites`; T-033's UI suite still passes.

## Tasks
- [ ] Point `modules/sites/data.ts` at T-027's repository; delete the sites fixtures.
- [ ] Hide Test connection, connection status and counts until a follow-up API ticket adds them.
- [ ] Tests: zero-sites redirect, switcher navigation, Add Site success and `wp_connection_failed`.

## Out of scope
- UI, layout and route structure (T-033).
- Site removal/archive. Cross-site report view.
- Per-user or per-client access control (R8.1 stands: single shared login).
