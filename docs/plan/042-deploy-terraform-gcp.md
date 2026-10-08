# T-042 Terraform for GCP

**Phase:** 5 · Deploy · **Status:** analyzed · **Size:** M
**Refs:** R8.1; architecture: Infrastructure, GCP services, Deployment and CI, Auth
**Depends on:** —

## Goal
One `terraform apply` sets up everything the app needs on GCP: Cloud Run for the API and web, Firestore, Firebase Auth with sign-up off, secrets, the image registry, and keyless deploys from GitHub.

## Analysis

### Inputs
| Value | |
| --- | --- |
| GCP project | `content-importer-adaptify` (already exists, billing linked) |
| Region | `us-central1` (architecture: Tier 1, full Cloud Run free tier) |
| GitHub repo | `ifindev/content-importer-adaptify` |
| State bucket | `gs://content-importer-adaptify-tfstate` |

### Manual steps, once
1. `gcloud auth login` and `gcloud auth application-default login` as the project owner.
2. Create the state bucket: `gcloud storage buckets create gs://content-importer-adaptify-tfstate --location=us-central1 --uniform-bucket-level-access`, then turn on versioning.
3. `terraform init`, `terraform apply`.
4. Add the secret values (they never go into Terraform state):
   - `CREDENTIAL_ENCRYPTION_KEY`: a new Fernet key (`uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`).
   - `INTERNAL_API_SECRET`: `openssl rand -base64 32`.
   - `printf '%s' "<value>" | gcloud secrets versions add <NAME> --data-file=-`.
5. Create the agency accounts in the Firebase console (Authentication → Users → Add user). See T-047.

### Layout: `infra/terraform/`
Flat files, no modules. `terraform.tfvars` is committed: it holds only `project_id`, `region` and `github_repo`, nothing secret. Commit `.terraform.lock.hcl`; ignore `.terraform/` and `*.tfstate*`.

**`main.tf`**
- `terraform` block: required `google` and `google-beta` providers (pinned major), `backend "gcs"` with the state bucket.
- Both providers with `project` and `region` from variables. `user_project_override = true` and `billing_project`, which the Firebase and Identity Platform resources need.
- `google_project_service` for: `run`, `firestore`, `artifactregistry`, `secretmanager`, `iam`, `iamcredentials`, `sts`, `firebase`, `identitytoolkit`, `cloudresourcemanager`, `serviceusage`. Set `disable_on_destroy = false`.
- `data "google_project"` for the project number.

**`run.tf`**
- Artifact Registry repo `app` (Docker, `us-central1`) with a cleanup policy: keep the 5 most recent versions of each image, delete the rest. This keeps storage under the 0.5 GB free tier.
- Service accounts:
  - `api`: `roles/datastore.user` (Firestore), `roles/firebaseauth.admin` (creates session cookies, and reads the user for `check_revoked=True`). `roles/secretmanager.secretAccessor` on `CREDENTIAL_ENCRYPTION_KEY` and `INTERNAL_API_SECRET`, bound **on each secret**, not on the project.
  - `web`: `roles/secretmanager.secretAccessor` on `INTERNAL_API_SECRET` only.
- `locals` with both URLs built from the project number: `https://api-${project_number}.us-central1.run.app` and `https://web-…`. The API needs the web URL (`WEB_BASE_URL`, for review links) and the web needs the API URL (`API_URL`); computing both avoids a dependency cycle between the two services.
- `google_cloud_run_v2_service` `api` and `web`:
  - First image: `us-docker.pkg.dev/cloudrun/container/hello` (placeholder; T-045 deploys the real images).
  - `scaling`: min 0, max 2. Max 2 caps cost and abuse; min 0 keeps it free (architecture decision on cold starts).
  - 1 vCPU, 512 MiB, `startup_cpu_boost = true`, CPU only during requests (the default).
  - `api` env: `APP_ENV=gcp`, `GOOGLE_CLOUD_PROJECT`, `WEB_BASE_URL`; secret env `CREDENTIAL_ENCRYPTION_KEY`, `INTERNAL_API_SECRET` (version `latest`).
  - `web` env: `APP_ENV=gcp`, `API_URL`; secret env `INTERNAL_API_SECRET`.
  - `lifecycle { ignore_changes = [template[0].containers[0].image, client, client_version] }`. The deploy workflow owns the image, and Terraform won't roll it back.
  - `deletion_protection = false`, so a clean `terraform destroy` works on this demo project.
- `google_cloud_run_v2_service_iam_member` with `roles/run.invoker` for `allUsers` on both. The API stays public: the web calls it from the server with the session cookie and `INTERNAL_API_SECRET`. Making it private needs an ID token from the web service, which is out of scope.

**`data.tf`**
- `google_firestore_database` `(default)`, `FIRESTORE_NATIVE`, location `us-central1`. If the project already has a default database, `terraform import` it instead of creating one.
- `google_firebase_project` (google-beta): turns Firebase on for the project.
- `google_identity_platform_config`:
  - `sign_in.email.enabled = true`, `password_required = true`.
  - `client.permissions.disabled_user_signup = true`. **This is the access control:** nobody can create an account through the public web API key, so the only accounts are the ones made in the console.
  - `authorized_domains`: `localhost` and the web `run.app` host. Email/password sign-in doesn't need them, but keeping them correct avoids a surprise if a provider is added later.
- `google_firebase_web_app` `web`, and `data "google_firebase_web_app_config"` for its `api_key` and `auth_domain`.

**`secrets.tf`**
- `google_secret_manager_secret` `CREDENTIAL_ENCRYPTION_KEY` and `INTERNAL_API_SECRET`, automatic replication, **no versions**. Values are added by hand (manual step 4).

**`github.tf`**
- `google_iam_workload_identity_pool` `github` and an OIDC provider `github`:
  - issuer `https://token.actions.githubusercontent.com`
  - `attribute_mapping`: `google.subject = assertion.sub`, `attribute.repository`, `attribute.ref`
  - `attribute_condition`: `assertion.repository == "ifindev/content-importer-adaptify" && assertion.ref == "refs/heads/main"`. Only pushes to `main` in this repo can deploy.
- Service account `deployer`:
  - `roles/run.developer` on the project.
  - `roles/artifactregistry.writer` on the `app` repo.
  - `roles/iam.serviceAccountUser` on the `api` and `web` service accounts only. Deploying a revision that runs as them needs it.
  - `roles/iam.workloadIdentityUser` for the pool principal set filtered on the repo.

**`outputs.tf`**
`api_url`, `web_url`, `wif_provider` (full resource name), `deployer_email`, `firebase_api_key`, `firebase_auth_domain`, `project_id`. T-045 copies these into GitHub repo variables.

### Notes
- **Firestore indexes:** none known. If the live flow logs a "query requires an index" error with a link, add a `google_firestore_index` here.
- **Identity Platform:** turning it on upgrades Firebase Auth on the project. It's free at this scale (one or two users).
- **`make agency-user`** stays for local use; it calls the emulator's sign-up endpoint, and the emulator doesn't enforce the sign-up setting.
- **The Firebase web API key is public by design.** It identifies the project; it isn't a secret. Sign-up being off is what stops strangers.

### Edge cases
| Case | Behavior |
| --- | --- |
| A Firestore database already exists in the project | `terraform import google_firestore_database.default projects/content-importer-adaptify/databases/(default)`. |
| Firebase already turned on in the console | Import `google_firebase_project` the same way. |
| Secret has no version yet when Cloud Run deploys | The revision fails to start. Add the values (manual step 4) and re-apply. Expected on the very first apply. |
| Someone calls `accounts:signUp` with the web API key | Refused by Identity Platform (`ADMIN_ONLY_OPERATION` or similar). |
| A deploy changed the image, then someone runs `terraform apply` | No change to the image (`ignore_changes`). |

### Decisions
- Access control is "sign-up off": only accounts created in the Firebase console can log in. No allowlist and no demo mode. Several agencies with self sign-up would be a multi-tenancy feature, not a setting. Update in this change:
  - spec R8.1: "The agency app needs a login once deployed. Accounts are created by the admin in the Firebase console; sign-up is off."
  - architecture Auth: add the sign-up rule, and that `make agency-user` is local only.
  - architecture "What Terraform creates": match this ticket (Firebase Auth, Workload Identity Federation, service accounts and their roles, the cleanup policy). Remove Vertex AI from the API list until Phase 7.

## Acceptance criteria
- [ ] `terraform apply` succeeds on the project, and a second `terraform plan` shows no changes.
- [ ] Both services answer on their `run.app` URLs with the hello page.
- [ ] `terraform output` gives every value T-045 needs.
- [ ] Sign-up is refused: `curl -X POST "https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=<firebase_api_key>" -H 'Content-Type: application/json' -d '{"email":"x@example.com","password":"secret123","returnSecureToken":true}'` returns an error.
- [ ] An account created in the console signs in through `accounts:signInWithPassword` with the same key.
- [ ] `terraform state pull | grep -i -E "fernet|INTERNAL_API_SECRET.*value"` finds no secret value.
- [ ] The `api` service account can't read any secret other than its two (try `gcloud secrets versions access` impersonating it on a third test secret, then delete the test secret).
- [ ] spec.md and architecture.md updated as listed in Decisions.

## Tasks
- [ ] Create the state bucket (manual).
- [ ] Write `main.tf`, `run.tf`, `data.tf`, `secrets.tf`, `github.tf`, `outputs.tf`, `variables.tf`, `terraform.tfvars`, `.gitignore`.
- [ ] Import an existing Firestore database or Firebase project if the first plan wants to create them.
- [ ] Apply, add secret values, apply again.
- [ ] Run the sign-up and sign-in checks.
- [ ] Add a short "Terraform" section to architecture (init, plan, apply, the manual steps).
- [ ] Update spec R8.1 and architecture Auth.

## Out of scope
- Budget, Pub/Sub and the kill switch (T-046).
- A custom domain for the app. The `run.app` URLs are used.
- A private API with IAM invoker auth.
- Running Terraform in CI.
- Vertex AI and the LangSmith secret (Phase 7).
