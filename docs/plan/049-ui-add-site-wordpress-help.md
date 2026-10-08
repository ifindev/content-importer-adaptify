# T-049 Add site: how to get a WordPress user and application password

**Phase:** 5 · Deploy · **Status:** done · **Size:** S
**Refs:** spec: Screens (Sites), WordPress integration
**Depends on:** —
**Improves:** T-032

## Goal
Someone adding a client site learns, in the dialog itself, how to create a WordPress user and its application password. They also learn that the password only works with that user's username. On the first live run, a mismatched username and password failed with only "Can't connect".

## Acceptance criteria
- [x] Under the username and password fields, a collapsed "How do I get a username and application password?" section opens to three steps: create an Author user, create its application password, paste it with that same username. A note follows: HTTPS, and security plugins that block the REST API.
- [x] When editing a site, "Leave the password empty to keep the current one." still shows.
- [x] `wp_connection_failed` says to check that the application password belongs to this username.
- [x] Checked by hand at 375, 768 and 1280px: no horizontal scroll, the section toggles by click and keyboard, the focus ring shows, and Escape closes the dialog. `pnpm typecheck` passes.
- [x] spec.md (Screens, Sites) and docs/deploy-vps.md (step 7) updated.

## Tasks
- [x] `SiteDialog.tsx`: replace the hint line with a `<details>` section, using the same pattern as the feedback toggle in `ArticleDetail.tsx`.
- [x] `error-messages.ts`: new `wp_connection_failed` text.
- [x] Update spec.md and deploy-vps.md.

## Out of scope
- Telling the causes of a failed connection apart. WordPress 7.1 answers every wrong login the same way.
- The design canvas. The section is collapsed by default, so the `AddSite` board's layout still holds.
