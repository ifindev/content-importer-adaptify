# T-050 Firestore index for the article list

**Phase:** 5 · Deploy · **Status:** in progress · **Size:** S
**Refs:** architecture: Setup (Firestore indexes)
**Depends on:** T-048
**Improves:** T-048

## Goal
The Articles page works on a real Firestore database. On the first live run, it showed "Something went wrong": the API's article list (filter by `status`, sort by `created_at` newest first) needs a composite index, and the emulator never asked for one.

## Acceptance criteria
- [ ] The index exists in the live project: `articles`, `status` ascending, `created_at` descending, scope Collection.
- [ ] The live Articles page loads, with and without a status filter, and the API logs show no "requires an index".
- [x] Terraform creates the index for the GCP target (`infra/terraform/data.tf`).
- [x] docs/deploy-vps.md step 1 has "Create the index", plus a troubleshooting row; architecture lists the index.

## Tasks
- [ ] Create the index in the Firebase console (manual).
- [x] Add `google_firestore_index` to Terraform.
- [x] Update docs/deploy-vps.md and architecture.md.
