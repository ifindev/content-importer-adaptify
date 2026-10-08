# T-038 Spec and ticket cleanup

**Phase:** 4 · Docs · **Status:** done · **Size:** S
**Refs:** spec (whole), workflow: Definition of Done, plan README
**Depends on:** T-037

## Goal
The spec and the tickets say what the code does. A spec-against-code audit (2026-10-08) found statements that drifted during the multi-site and wiring work, and ticket boxes that no longer matched reality.

## Analysis

### Spec corrections
- **WordPress auth:** credentials are checked when a site is added, edited or tested, not at startup.
- **Rate limit:** the client IP arrives in `X-Client-IP` with a shared secret, not a trusted `X-Forwarded-For` (T-037).
- **Lifecycle:**
  - diagram and table: Scheduled → Approved (unschedule), Scheduled → Failed, Failed → Scheduled by a new date; Scheduled → Draft removed;
  - Approval rules: locking includes Scheduled, unschedule keeps approval, and delete trashes a leftover WordPress draft;
  - R2.2, R2.3, R4.3 and R5.3 reworded; R5.4 is per site.
- **Data model:** `sent_for_review_at`; `version` grows on every edit; `client_comment` is also cleared on approve; `approved_version` is cleared on a reset; `unscheduled` events; `reset_from` data.
- **API:**
  - add `GET /health` and `unschedule`;
  - Retry's `publish_at_in_past`;
  - the error `message` field.
- **Decisions:**
  - "dates only after approval" moves from open question to Decision;
  - the stale "the README records this" pointer is removed.
- **Screens:** the Sites row cites E8; the Article detail actions and the "Editing after approval" bullet match read-only Scheduled.

### Tickets and workflow
- T-019 and T-027: dropped items struck instead of left as open boxes.
- T-028, T-029, T-032, T-033: boxes the code already meets are ticked. T-029 drops Playwright and `make e2e`: the MVP has no end-to-end suite, and the full flow is checked by hand.
- `workflow.md` Definition of Done: the Postman item is removed (Swagger is the reference), and the frontend has no automated UI tests.
- `architecture.md`: the client-IP mechanism and `INTERNAL_API_SECRET`; the testing table's end-to-end row becomes the by-hand check.

## Acceptance criteria
- [x] Every stale statement from the audit is corrected or removed.
- [x] No done ticket keeps an open box for dropped work.
