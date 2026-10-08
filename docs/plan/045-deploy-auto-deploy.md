# T-045 Auto-deploy to Cloud Run

**Phase:** 5 · Deploy · **Status:** on hold (no GCP billing account; T-048 deploys to the VPS meanwhile) · **Size:** S
**Refs:** R8.1, R8.2; spec: API endpoints (rate-limit Decision); architecture: Deployment and CI
**Depends on:** T-040, T-041, T-042, T-044

## Goal
A push to `main` that passes CI is live on Cloud Run a few minutes later, with no manual step. This ticket also runs the first full flow on the live app against `wp.aiwitharifin.com`.

## Analysis

### Deploy job in `ci.yml`
A `deploy` job in the same workflow, not a separate file: it reuses the CI jobs as its gate, with no `workflow_run` setup.
- `needs: [server, web, api-types]`.
- `if: github.event_name == 'push' && github.ref == 'refs/heads/main'`. Pull requests never deploy.
- `permissions: { id-token: write, contents: read }`. The ID token is what Workload Identity Federation exchanges.
- `concurrency: { group: deploy, cancel-in-progress: false }`. Deploys queue; one never stops halfway.

Steps:
1. `actions/checkout`.
2. `google-github-actions/auth` with `workload_identity_provider: ${{ vars.GCP_WIF_PROVIDER }}` and `service_account: ${{ vars.GCP_DEPLOYER_SA }}`. No JSON key anywhere.
3. `google-github-actions/setup-gcloud`.
4. `gcloud auth configure-docker us-central1-docker.pkg.dev`.
5. Build and push the server: `docker build --target prod -t us-central1-docker.pkg.dev/<project>/app/api:${{ github.sha }} server/`, then push.
6. Build and push the web the same way, with `--build-arg NEXT_PUBLIC_FIREBASE_API_KEY=${{ vars.FIREBASE_API_KEY }}`, `…_AUTH_DOMAIN`, `…_PROJECT_ID`.
7. `gcloud run deploy api --image …/api:<sha> --region us-central1`, then the same for `web`. The API goes first, so a new web never calls an older API.

Only the image changes. Env vars, secrets, scaling and the service account stay as Terraform set them (T-042's `ignore_changes` covers the image only).

### GitHub repo variables
Settings → Secrets and variables → Actions → **Variables** (none are secret):

| Variable | From |
| --- | --- |
| `GCP_PROJECT_ID` | `content-importer-adaptify` |
| `GCP_WIF_PROVIDER` | `terraform output wif_provider` |
| `GCP_DEPLOYER_SA` | `terraform output deployer_email` |
| `FIREBASE_API_KEY` | `terraform output firebase_api_key` |
| `FIREBASE_AUTH_DOMAIN` | `terraform output firebase_auth_domain` |
| `FIREBASE_PROJECT_ID` | `content-importer-adaptify` |

### Client IP on Cloud Run
Client routes are rate-limited per client IP (spec: API endpoints Decision). The web reads the visitor's IP from the last `X-Forwarded-For` entry (`web/lib/api-server.ts:39-41`). A `ponytail:` comment there says this assumes one proxy and must be rechecked on Cloud Run.
- Check: open the review page from two different networks (for example Wi-Fi and phone data) and confirm the API logs two different client IPs, both matching the real public IPs.
- If Cloud Run's last entry is its own hop, not the visitor, change the index to the right entry and update the comment and architecture.

### Cookies on `run.app`
`run.app` is on the Public Suffix List, so each service's host is its own site: the `session` cookie set by `web-…run.app` stays on that host. The web sets it with `secure` because `APP_ENV` isn't `local` (`auth.mutations.ts:25-60`). Nothing to change; the live login confirms it.

### Rollback
Written into architecture:
- List revisions: `gcloud run revisions list --service web --region us-central1`.
- Send all traffic back: `gcloud run services update-traffic web --to-revisions <previous-revision>=100 --region us-central1`.
- The next deploy from `main` sends traffic to the new revision again.

### First live run (by hand, after the first deploy)
Use your own account (T-047 creates the demo one).
1. Sign in on the web URL.
2. Add site: `https://wp.aiwitharifin.com`, user `content-importer`, the Author's app password (T-043). The connection test passes.
3. Paste an article, upload a `.docx`.
4. Send for review, copy the review link, open it in a private window at 375px wide: approve one article, request changes on the other.
5. Set a date 6 minutes ahead on the approved one; wait; it shows Published with the live URL, and the URL opens the post.
6. Unschedule and reschedule a second article; the post moves to WordPress's trash and a new one is created (check as WordPress admin).
7. Push a trivial commit; after the deploy, the same review link still opens (proves T-040).
8. Open the Report screen.

### Edge cases
| Case | Behavior |
| --- | --- |
| A deploy fails halfway (API deployed, web not) | The API change is backward compatible by habit (the web is the only client). Re-run the job, or roll back the API. |
| A revision fails to start (missing secret, crash) | Cloud Run keeps serving the previous revision; the job fails at `gcloud run deploy`. |
| Cold start on the first visit after idle | A few seconds on the first page (two services wake up). Accepted (architecture: min instances 0). |

### Decisions
- Update architecture "Deployment and CI": the deploy job, repo variables, image tags by commit SHA, rollback, and the client-IP finding.

## Acceptance criteria
- [ ] A commit to `main` deploys both services with no manual step, and the web URL serves it.
- [ ] Images in Artifact Registry are tagged with the commit SHA; the cleanup policy keeps 5.
- [ ] Pull requests run CI but never `deploy`.
- [ ] The first live run above passes, every step.
- [ ] A review link copied before a deploy still works after it.
- [ ] The API logs show the real visitor IP for review routes (or the fix is in).
- [ ] A rollback to the previous revision works once, by hand.
- [ ] architecture.md updated.

## Tasks
- [ ] Add the repo variables from `terraform output`.
- [ ] Add the `deploy` job to `ci.yml`.
- [ ] Push; fix anything in the first deploy.
- [ ] Run the first live run; fix any production-only issue (indexes, env, cookies) in this ticket or a new one.
- [ ] Check the client IP; fix it if needed.
- [ ] Try one rollback.
- [ ] Update architecture.md.

## Out of scope
- Staging or preview environments.
- Traffic splitting or canary releases.
- A custom domain for the web app.
