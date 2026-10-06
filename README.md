# Content Importer for Adaptify SEO

An MVP of the "import existing content" feature from Adaptify SEO's public roadmap:

> Import articles that have been written somewhere else. Then have Adaptify SEO handle the customer approval, scheduling, publishing, and reporting.

Agencies paste or upload articles written outside Adaptify. Their clients approve them through a private review link, and approved articles are scheduled and published to WordPress, with a workflow report on top.

**Status:** Phase 1, Bootstrap. See [the plan](docs/plan/README.md).

## Docs

| Doc | What it covers |
| --- | --- |
| [Spec](docs/spec.md) | What the system does: scope, journeys, lifecycle, requirements, API |
| [Architecture](docs/architecture.md) | How the code is organized: server, frontend, auth, infra, testing, cost |
| [Workflow](docs/workflow.md) | How the work is planned and done: tickets, conventions, Definition of Done |
| [Plan](docs/plan/README.md) | Phases and the master list of tickets |

## Stack

Python 3.12 · FastAPI · Firestore · Firebase Auth · Next.js · shadcn/ui · WordPress REST API · GCP Cloud Run · Terraform. Tooling: uv, pnpm, Docker Compose.

## Getting started

Added in Phase 2 (local infra), when `make up` runs the full stack.
