# T-048 Deploy the app to the VPS, with auto-deploy

**Phase:** 5 · Deploy · **Status:** in progress · **Size:** M
**Refs:** R8.1, R8.2; architecture: Infrastructure, Auth, Deployment and CI, Cost and limits
**Depends on:** T-041, T-043, T-044
**Puts on hold:** T-042, T-045, T-046 (they need GCP billing)

## Goal
The app runs on the VPS next to WordPress at `https://importer-app.aiwitharifin.com`, and every push to `main` that passes CI goes live with no manual step. No GCP billing account is needed. GCP stays a second target: the same images and Terraform deploy there once billing works.

## Analysis

### Why
GCP refused the card (a virtual card), so the project has no billing account. Cloud Run, Secret Manager, Artifact Registry, Terraform's state bucket and the budget kill switch all need one. Firestore and Firebase Auth work on Firebase's free Spark plan, so they stay; only compute moves.

### What replaces what
| Was (GCP) | Now |
| --- | --- |
| Cloud Run `api`, `web` | `infra/app/docker-compose.yml` on the VPS; web on `127.0.0.1:3000`, API on `127.0.0.1:8000`; the web calls the API on the compose network |
| Secret Manager | `~/app/.env` (`chmod 600`) |
| Service-account identity on Cloud Run | A Firebase service-account key file, mounted read-only |
| Artifact Registry | GHCR, tagged with the commit SHA |
| Workload Identity Federation | An SSH deploy key (GitHub secret) plus the job's own `GITHUB_TOKEN` for GHCR |
| Terraform | Manual setup steps in architecture (Firebase setup, VPS setup) |
| Budget kill switch | Not needed: Spark can't bill, the VPS is flat |
| `run.app` URLs | `importer-app.aiwitharifin.com` (web) and `importer-api.aiwitharifin.com` (API, for `/docs` and `/health`) via nginx + certbot |
| `APP_ENV=gcp` | `APP_ENV=prod` |

### Access control
Identity Platform's `disabled_user_signup` was the access control (T-042). On Spark it may not be available, so the API checks an allowlist: `AGENCY_EMAILS`, comma-separated, case-insensitive. `POST /auth/session` refuses a token whose email isn't listed (`401 invalid_token`), so no session cookie is ever minted for it, and every agency route needs that cookie. Required when `APP_ENV=prod`; the API refuses to start without it.

### Auto-deploy
A `deploy` job in `ci.yml` after `server`, `web` and `api-types`, only on a push to `main`:
1. Build both `prod` images, push to GHCR with `GITHUB_TOKEN` (`packages: write`).
2. `scp` the compose file to `~/app`, log the VPS in to GHCR with the same token over stdin, `docker compose pull && up -d` with `IMAGE_TAG=<sha>`, log out, prune app images older than a week.

The workflow's `cancel-in-progress` is off on `main`, so a new push queues behind a running deploy instead of killing it.

### Client IP
nginx appends the visitor's address to `X-Forwarded-For`; the web reads the last entry (`lib/api-server.ts`). One proxy, as the existing `ponytail:` comment assumes.

### Edge cases
| Case | Behavior |
| --- | --- |
| Someone signs up through the public API key | The account exists in Firebase, but `/auth/session` refuses it. |
| A deploy fails at `compose pull` | Containers keep running the previous images; the job fails. |
| A new image crashes on start | `restart: unless-stopped` loops it; roll back with `IMAGE_TAG=<older sha> docker compose up -d`. |
| VPS reboots | Both containers come back on their own. |
| Upload over 32 MB | nginx answers 413; the upload screen already refuses over 30 MB first. |
| Spark daily quota exceeded | Firestore calls fail until the next day; nothing is billed. |

### Decisions
- Updated in this change: spec R8.1 and the risk table; architecture Overview, Tech stack, folder layout, Auth, Infrastructure, Deployment and CI, Cost and limits; README Deploy.
- The step-by-step guide is general (`docs/deploy-vps.md`, `<domain>` placeholders); `make vps-setup` takes `APP_DOMAIN` and `API_DOMAIN` and fills in the nginx sites. Dokploy and similar were considered and skipped: their proxy wants ports 80 and 443, which nginx already uses for WordPress.
- Two deploy targets, VPS and GCP, sharing the `prod` images and `APP_ENV=prod`. `infra/terraform/` stays: `APP_ENV` is now `prod` there, and the API gets `AGENCY_EMAILS` from the `agency_emails` variable.
- Phase 7's Vertex AI needs billing; revisit the provider then.

## Acceptance criteria
- [x] `APP_ENV=prod` replaces `gcp`; the API won't start in prod without `AGENCY_EMAILS`.
- [x] An email not in `AGENCY_EMAILS` can't get a session (unit tests).
- [x] `infra/app/` has the compose file, `.env.example` and the `app` and `api` nginx sites.
- [x] `ci.yml` has the `deploy` job; `actionlint` passes.
- [ ] Firebase set up on Spark: Firestore, Email/Password, web app, service-account key.
- [ ] VPS set up: DNS, `~/app`, nginx and certificate, deploy key.
- [ ] GitHub variables and secrets added.
- [ ] A push to `main` deploys with no manual step, and the web URL serves it.
- [ ] Signing in with an unlisted account is refused on the live app.
- [ ] The live full flow (T-045's "First live run", steps 1–8) passes against `wp.aiwitharifin.com`.
- [ ] The API logs show the real visitor IP on review routes.
- [ ] One rollback by `IMAGE_TAG` works.
- [x] spec.md, architecture.md and README updated.

## Tasks
- [x] Rename `gcp` to `prod`; add `AGENCY_EMAILS` and its tests.
- [x] Write `infra/app/`; point `infra/terraform/` at `APP_ENV=prod` and `AGENCY_EMAILS`.
- [x] Add the `deploy` job.
- [x] Update the docs.
- [ ] Firebase setup (manual).
- [x] `make vps-setup` (`infra/app/setup.sh`) automates the VPS and GitHub setup.
- [ ] Run it (after the Firebase setup and DNS).
- [ ] First push; fix anything production-only.
- [ ] Live run, client-IP check, rollback.

## Out of scope
- Zero-downtime deploys (a few seconds of restart per deploy is fine).
- Monitoring and alerting beyond `docker compose logs`.
- Integration tests in CI.
