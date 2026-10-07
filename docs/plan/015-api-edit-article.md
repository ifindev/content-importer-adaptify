# T-015 Edit article

**Phase:** 3 · API · **Status:** analyzed · **Size:** S
**Refs:** R2.1–R2.3, spec: Approval rules, API endpoints (Agency)
**Depends on:** T-013

## Goal
The agency edits an article's title, slug, and body while it's editable, and editing an Approved or Scheduled article resets it to Draft so approval always tracks the exact text the client saw.

## Analysis

### Flow
1. `PATCH /articles/{id}` with any of `title`, `slug`, `body_html`.
2. Allowed only from `Draft` or `Changes requested` (R2.2) — **except** the approval-reset case: editing from `Approved` or `Scheduled` is also allowed, and the use case itself demotes the article to `Draft` first (R2.3), bumping `version`.
3. From any other status (`Awaiting approval`, `Published`, `Failed`), editing is refused.
4. Every save bumps `version`; `approved_version` is untouched (it records what was approved — `version` moves past it, which is exactly what makes `version > approved_version` mean "unapproved changes exist").
5. An `edited` event is appended; if the reset happened, so does a follow-on note in the same event's `data` (no separate event type needed — `edited` carries `{reset_from: "approved" | "scheduled"}` when applicable).

### API
`PATCH /articles/{id}`

| Field | Type | Rules |
| --- | --- | --- |
| `title` | string, optional | 1–200 chars if present |
| `slug` | string, optional | lowercase, `[a-z0-9-]+`, if present |
| `body_html` | string, optional | non-empty if present, max 2 MB, cleaned with the same `html_rules` allowed-tag list as import |

| Case | Status | Body |
| --- | --- | --- |
| Edited from Draft/Changes requested | 200 | `ArticleDetail` |
| Edited from Approved/Scheduled (reset) | 200 | `ArticleDetail` (status now `Draft`) |
| Edited from Awaiting approval/Published/Failed | 409 | `{code: "not_editable"}` |
| Not found | 404 | `{code: "not_found"}` |
| No fields supplied | 422 | `{code: "empty_update"}` |
| `body_html` over 2 MB | 413 | `{code: "payload_too_large"}` |

### Core
- `core/use_cases/edit_article.py`: `edit_article(id, title=None, slug=None, body_html=None)`. Checks status via `lifecycle.py`'s allowed-edit set (`{Draft, ChangesRequested, Approved, Scheduled}`), applies the reset through `lifecycle.transition` when status was `Approved`/`Scheduled`, re-cleans `body_html` if given, increments `version`, saves, appends event.
- Scheduled-specific WordPress side effect (moving the WP post to draft, R4.3) is **not** this ticket's job — it belongs to T-020 (Schedule), which owns the `Publisher` port. This ticket only flips the Firestore status; T-020 wires the WordPress call in. Note this dependency so T-020 doesn't skip it.

### Edge cases
| Case | Behavior |
| --- | --- |
| Edit with identical values (no-op edit) | Still bumps `version` and appends `edited` — simplest rule, no special-casing a no-op |
| Slug collision with another article on the same site | Not checked here — WordPress is the source of truth for slug uniqueness; a collision surfaces as a Failed publish (T-020), not an edit-time error |

### Decisions
- The WordPress "move to draft on edit" side effect (R4.3) is split into T-020 rather than duplicated here, since it needs the `Publisher` port this ticket doesn't otherwise touch. **Follow-up for T-020:** its acceptance criteria must include "editing a Scheduled article (via this ticket's endpoint) moves the WP post to draft," tested end-to-end once both tickets exist.

## Acceptance criteria
- [ ] Editing a Draft article updates fields and bumps `version`.
- [ ] Editing an Approved article moves it to Draft and bumps `version`.
- [ ] Editing a Scheduled article moves it to Draft and bumps `version` (WordPress side effect deferred to T-020, called out there).
- [ ] Editing an Awaiting approval, Published, or Failed article returns 409 `not_editable`.
- [ ] `PATCH` with no fields returns 422.
- [ ] Swagger and Postman updated.

## Tasks
- [ ] `core/use_cases/edit_article.py`.
- [ ] `api/routes/articles.py`: add `PATCH /articles/{id}`.
- [ ] `api/schemas.py`: `ArticleUpdate`.
- [ ] Unit tests: status × edit allowed/refused table from Analysis; reset bumps `version` and changes status; event recorded.
- [ ] Integration test: Firestore emulator round-trip.
- [ ] `pnpm gen:api`.

## Out of scope
- Moving the WordPress post to draft on reset (T-020).
- Slug uniqueness validation.
