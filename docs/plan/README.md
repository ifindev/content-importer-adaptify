# Plan

Phases and the master list of tickets. How tickets work: [workflow.md](../workflow.md). Ticket template: [_template.md](_template.md).

**Current phase:** 2. Local infra

## Phases

| # | Phase | Goal | Done when |
| --- | --- | --- | --- |
| 1 | Bootstrap | Both apps exist with their tooling and folder structure | Backend lint, import-linter and tests pass; the web app builds and lints; API types generate from `openapi.json` |
| 2 | Local infra | The whole stack runs locally, and the riskiest link (publishing to WordPress) is proven | `make up` starts everything; the API creates a scheduled post in local WordPress and it goes live after `make wp-cron` |
| 3 | API | Every P0 and P1 endpoint, by epic: lifecycle core → import → review → schedule → sync → report | The spec's end-to-end test passes through the API alone: paste → send → approve → schedule → wp-cron → Published |
| 4 | Frontend | Every screen: data layer → design per screen → build on real data | The full flow works in the browser, agency and client |
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
| T-002 | [Backend skeleton](002-bootstrap-backend-skeleton.md) | architecture: Backend | done |
| T-003 | [Next.js scaffold](003-bootstrap-nextjs-scaffold.md) | architecture: Frontend | done |
| T-004 | [Frontend setup](004-bootstrap-frontend-setup.md) | architecture: Frontend | done |
| T-005 | [API type generation](005-bootstrap-api-type-generation.md) | architecture: Frontend | done |

### Phase 2: Local infra

| ID | Ticket | Refs | Status |
| --- | --- | --- | --- |
| T-006 | [Compose: api and web](006-infra-compose-api-web.md) | architecture: Local setup | analyzed |
| T-007 | [Local WordPress](007-infra-local-wordpress.md) | spec: WordPress integration | analyzed |
| T-008 | [Firebase emulators](008-infra-firebase-emulators.md) | architecture: Auth, Local setup | analyzed |
| T-009 | [WordPress publish check](009-infra-wordpress-publish-check.md) | spec: WordPress integration | analyzed |

### Phase 3: API

Tickets are written when Phase 2 is nearly done.

### Phase 4: Frontend

Tickets are written when Phase 3 is nearly done.

### Phase 5: Deploy

Tickets are written when Phase 4 is nearly done.

### Phase 6: Demo readiness

Tickets are written when Phase 5 is nearly done.

### Phase 7: AI (P2)

Tickets are written when Phase 6 is nearly done.
