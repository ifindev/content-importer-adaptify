# Workflow

How the work on this project is planned, done, and kept in sync with the docs.

## Doc map

| Doc | Answers | Changes when |
| --- | --- | --- |
| [spec.md](spec.md) | **What** the system does: scope, journeys, lifecycle, requirements, data model, API endpoints | A product or behavior decision changes |
| [architecture.md](architecture.md) | **How** the code is organized: server, frontend, auth, infra, testing, cost | The structure or a technical decision changes |
| [plan/README.md](plan/README.md) | **When**: phases and the master list of tickets | A ticket is added or changes status |
| `workflow.md` (this file) | **How we work**: tickets, conventions, Definition of Done | The process changes |

## Phases

| # | Phase | In short |
| --- | --- | --- |
| 1 | Bootstrap | Backend skeleton and Next.js app, fully set up, with folder structure |
| 2 | Local infra | Docker compose with emulators and WordPress; a real publish to WordPress works |
| 3 | API | Every endpoint, by epic; the end-to-end test passes through the API alone |
| 4 | Frontend | Every screen's UI on fixtures → data layer → wire each screen to real data |
| 5 | Deploy | GCP, VPS WordPress, CI |
| 6 | Demo readiness | README, seed data |
| 7 | AI (P2) | Change drafting |

Goals and "done when" for each phase are in [plan/README.md](plan/README.md).

## Tickets

- **One ticket = one vertical slice**: one thing a user or developer can do, covering everything it needs (endpoint, use case, data, UI, tests). Not one layer.
- **Analyze just in time.** Write and analyze tickets for the next phase only, when the current phase is nearly done. What you learn building one phase changes the next.
- **The Analysis section is where unclear details get settled.** Its job is to find gaps, like a missing field or an unhandled edge case. If analysis changes a decision, update the spec or architecture doc.
- **Size:** a ticket fits in about a day. If its analysis gets long, split it.
- **Simple tickets** (setup, config) keep only Goal, Acceptance criteria and Tasks.
- **Template:** [plan/_template.md](plan/_template.md).

### Statuses

`todo` → `analyzed` → `in progress` → `done`

- `todo`: listed, not yet thought through.
- `analyzed`: Analysis, Acceptance criteria and Tasks written. Ready to build.
- `in progress`: being built.
- `done`: all acceptance criteria pass and the docs are updated.

The status lives in the master list, [plan/README.md](plan/README.md), and in the ticket header.

### Naming

- **File:** `docs/plan/<seq>-<area>-<slug>.md`, flat, for example `012-api-client-approves.md`.
- **`<seq>`:** one global sequence, three digits, never reused. Gaps are fine.
- **`<area>`:** `bootstrap`, `infra`, `api`, `ui`, `deploy`, `demo`, or `ai`.
- **ID:** `T-012`.
- **Branch:** none. During the MVP all work is committed on `main`; the ticket ID lives in the commit scope.
- **Commit:** `feat(T-012): client approve endpoint` (also `fix`, `docs`, `chore`, `test`, `refactor`).

**Improvements to finished work** are new tickets with the next number and an `Improves: T-012` line in the header. They're listed under the phase in which they're worked, not the phase of the original ticket. Phase membership lives in the master list, not in folders.

## Definition of Done

### API tickets

1. **Data model change** applied, and the spec's Data model section updated.
2. **Request and response schemas** (Pydantic) with validation, `description`, and `examples`. These produce the Swagger docs at `/docs`, so there's no separate docs step.
3. **Unit tests first** for the rules: lifecycle transitions and use cases, run with in-memory and scripted adapters. Write the test tables from the ticket (status × action, error codes) before the code.
4. **Repository, use case, and route**, following the import rules in [architecture.md](architecture.md#import-rules).
5. **Integration tests** against the Firestore emulator and the local WordPress container.
6. **Swagger** at `/docs` shows the endpoint correctly. It is the API reference; there is no Postman collection.
7. **Types regenerated** for the frontend (`pnpm gen:api`) if the API changed.

### Frontend tickets

1. **Data layer:** one ticket for the whole app: `*.queries.ts` and `*.mutations.ts` for every module, typed from `lib/api/schema.ts`. Mutations return `{ ok, code }` for expected errors.
2. **UI ticket:** one ticket builds every screen from the design canvas (made with `/design`) on fixtures typed from `lib/api/schema.ts`, in every state (loading, empty, error codes from the API tickets, sync warnings, banners), checked by hand in the browser (no Playwright; see CLAUDE.md). Pages read data only through `modules/<m>/data.ts` and write only through `modules/<m>/actions.ts`.
3. **Wiring tickets** may group several screens. Each points its modules' `data.ts` and `actions.ts` at the data layer, deletes the fixtures, and checks every flow and error code against the real API.
4. **Responsive:** every screen works at 375, 768, and 1280px with no horizontal scroll, and is usable by keyboard.
5. **No automated UI tests** (CLAUDE.md): no Playwright or other end-to-end suite, and no new vitest tests. A frontend ticket is checked by hand in the browser plus `pnpm typecheck`.

Frontend tickets may be size L.

### Every ticket

- Acceptance criteria pass.
- `spec.md` or `architecture.md` updated **in the same change** if behavior or structure changed.
- Ticket status set to `done` in its header and in the master list.

## Keeping docs true

The spec and the architecture doc describe the system as it is, not as it was planned. When the code shows a doc was wrong, fix the doc in the same commit. A ticket that changes behavior without updating the spec isn't done.
