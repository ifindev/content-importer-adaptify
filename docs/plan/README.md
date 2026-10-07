# Plan

Phases and the master list of tickets. How tickets work: [workflow.md](../workflow.md). Ticket template: [_template.md](_template.md).

**Current phase:** 3. API

## Phases

| # | Phase | Goal | Done when |
| --- | --- | --- | --- |
| 1 | Bootstrap | Both apps exist with their tooling and folder structure | Backend lint, import-linter and tests pass; the web app builds and lints; API types generate from `openapi.json` |
| 2 | Local infra | The whole stack runs locally, and the riskiest link (publishing to WordPress) is proven | `make up` starts everything; the API creates a scheduled post in local WordPress and it goes live after `make wp-cron` |
| 3 | API | Every P0 and P1 endpoint, by epic: lifecycle core → import → review → schedule → sync → report | The spec's end-to-end test passes through the API alone: paste → send → approve → schedule → wp-cron → Published |
| 4 | Frontend | Every screen's UI on fixtures → data layer → wire each screen to real data | The full flow works in the browser, agency and client |
| 5 | Deploy | The app runs on GCP against the VPS WordPress | The live URL runs the full flow; budget alert and kill switch are in place |
| 6 | Demo readiness | Someone new can run it | A new person runs the full flow from the README alone; seed data covers every status |
| 7 | AI (P2) | AI change drafting | A sample draft passes hand review; the spend limit refuses past $2 |

### Requirements by phase

| Phase | Requirements |
| --- | --- |
| 3 | API side of every P0 and P1 requirement in E1–E6 (R1.1–R6.5), plus R8.2 |
| 4 | UI side of the same requirements |
| 5 | R8.1 |
| 7 | R7.1–R7.3 |
| Not planned | R7.4, R7.5 (Backlog) |

## Tickets

### Phase 1: Bootstrap

| ID | Ticket | Refs | Status |
| --- | --- | --- | --- |
| T-001 | [Repo layout](001-bootstrap-repo-layout.md) | — | done |
| T-002 | [Server skeleton](002-bootstrap-backend-skeleton.md) | architecture: Server | done |
| T-003 | [Next.js scaffold](003-bootstrap-nextjs-scaffold.md) | architecture: Frontend | done |
| T-004 | [Frontend setup](004-bootstrap-frontend-setup.md) | architecture: Frontend | done |
| T-005 | [API type generation](005-bootstrap-api-type-generation.md) | architecture: Frontend | done |

### Phase 2: Local infra

| ID | Ticket | Refs | Status |
| --- | --- | --- | --- |
| T-006 | [Compose: api and web](006-infra-compose-api-web.md) | architecture: Local setup | done |
| T-007 | [Local WordPress](007-infra-local-wordpress.md) | spec: WordPress integration | done |
| T-008 | [Firebase emulators](008-infra-firebase-emulators.md) | architecture: Auth, Local setup | done |
| T-009 | [WordPress publish check](009-infra-wordpress-publish-check.md) | spec: WordPress integration | done |
| T-010 | [Rename backend to server](010-rename-backend-to-server.md) | architecture: Server | done |
| T-011 | [Adapter logging convention](011-adapter-logging-convention.md) | architecture: Server (Logging) | done |

### Phase 3: API

| ID | Ticket | Refs | Status |
| --- | --- | --- | --- |
| T-012 | [Auth session](012-api-auth-session.md) | R8.1, architecture: Auth | done |
| T-013 | [Lifecycle core: model, Firestore repository, list and detail](013-api-lifecycle-core.md) | R2.4 | done |
| T-014 | [Import articles](014-api-import-articles.md) | R1.1–R1.7 | done |
| T-015 | [Edit article](015-api-edit-article.md) | R2.1–R2.3 | done |
| T-016 | [Review link](016-api-review-link.md) | R3.1, R3.2, R3.7 | done |
| T-017 | [Send for review and pull back](017-api-send-for-review-pull-back.md) | R3.6 | done |
| T-018 | [Client review page](018-api-client-review-page.md) | R3.3, R6.5, R8.2 | done |
| T-019 | [Client approve and request changes](019-api-client-approve-request-changes.md) | R3.4, R3.5 | done |
| T-020 | [Schedule, retry, and the WordPress publisher](020-api-schedule-publish.md) | R4.1–R4.5 | done |
| T-021 | [WordPress status sync](021-api-status-sync.md) | R5.1–R5.4 | done |
| T-022 | [Agency report](022-api-agency-report.md) | R6.1–R6.4 | done |
| T-023 | [Fail fast on Firestore startup failure in GCP](023-api-firestore-fallback-guard.md) | architecture: GCP services | done |
| T-024 | [Consolidate API exception handling](024-api-error-handler-refactor.md) | architecture: Server folder layout | done |
| T-025 | [Group Swagger by workflow](025-api-swagger-sections.md) | architecture: Server folder layout | done |
| T-030 | [Split api/schemas.py by route](030-api-schemas-split.md) | architecture: Server folder layout | done |
| T-031 | [Multi-site: sites collection, siteId-scoped routes, encrypted credentials](031-api-multi-site-sites-collection.md) | spec: Data model, Out of scope | done |

### Phase 4: Frontend

| ID | Ticket | Refs | Status |
| --- | --- | --- | --- |
| T-026 | [Access control and app shell](026-ui-access-shell.md) | R8.1, R8.2, architecture: Auth | in progress |
| T-033 | [UI revamp: every screen on fixtures](033-ui-revamp-all-screens.md) | spec: Screens, design canvas | analyzed |
| T-032 | [Sites: wiring for the switcher, sites list and Add Site](032-ui-site-switcher-add-site.md) | spec: Screens, E8 Access | analyzed |
| T-027 | [API data layer](027-ui-data-layer.md) | E1–E6, architecture: Frontend | analyzed |
| T-028 | [Agency screens: wiring](028-ui-agency-screens.md) | E1, E2, E4, R3.2, R3.5–R3.7, R5.1–R5.3, R6.1–R6.4 | analyzed |
| T-029 | [Client review: wiring and full-flow test](029-ui-client-review-e2e.md) | R3.3–R3.5, R6.5, R8.2 | analyzed |

Build order for this phase: T-026 (in progress) → T-033 (all UI on fixtures, no API needed) → T-027 → T-032 → T-028 → T-029. T-031 (multi-site API) is already built, so the generated schema covers every endpoint, sites included. UI first: T-033 builds and tests every screen on fixtures typed from that schema; the wiring tickets then swap each module's fixtures for T-027's functions. Design canvas: [claude.ai artifact](https://claude.ai/artifact/QCpMywgpasGi231uuWrAMn), offline copy `design/canvas.html`.

### Phase 5: Deploy

Tickets are written when Phase 4 is nearly done.

### Phase 6: Demo readiness

Tickets are written when Phase 5 is nearly done.

### Phase 7: AI (P2)

Tickets are written when Phase 6 is nearly done.
