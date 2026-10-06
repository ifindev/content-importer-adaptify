# T-008 Firebase emulators

**Phase:** 2 · Local infra · **Status:** analyzed · **Size:** M
**Refs:** architecture: Auth, Infrastructure › Local setup; spec: Open questions (session cookies)
**Depends on:** T-006

## Goal
Firestore and Firebase Auth run locally in Docker, the API reaches both with the real SDK and no code swap, and we know whether the session-cookie auth flow works against the emulator.

## Analysis

### Decisions
- **One `firebase` service** built from a small Dockerfile: Node + Java (the Firestore emulator needs a JRE) + `firebase-tools`. It runs `firebase emulators:start --only firestore,auth`.
- **Project ID `demo-content-importer`.** The `demo-` prefix tells the SDKs it's emulator-only, so no real credentials or GCP project are needed locally.
- **Ports:** Firestore `8081` (host), Auth `9099`, Emulator UI `4000`. Firestore's default `8080` would clash with WordPress on the host.
- **Data persists** across restarts with `--import`/`--export-on-exit` into a named volume. `make firebase-reset` clears it.
- The API finds the emulators through env vars: `FIRESTORE_EMULATOR_HOST=firebase:8081`, `FIREBASE_AUTH_EMULATOR_HOST=firebase:9099`, `GOOGLE_CLOUD_PROJECT=demo-content-importer`.

### Session cookie check
Answer the spec's open question with a throwaway script (not kept as a test):
1. Create a user in the Auth emulator.
2. Sign in through the emulator's REST endpoint to get an ID token.
3. `firebase_admin.auth.create_session_cookie(id_token, expires_in=...)`.
4. `firebase_admin.auth.verify_session_cookie(cookie)` returns the user.

If it fails, record the fallback in the spec and architecture docs. Likely fallback: locally, the API accepts the ID token itself in place of the session cookie.

## Acceptance criteria
- [ ] `make up` starts the emulators; the Emulator UI shows at `http://localhost:4000`
- [ ] From the api container, `firebase_admin` / `google-cloud-firestore` write and read a document with no credentials configured
- [ ] Session cookie check done; the spec's open question is ticked with the answer
- [ ] Emulator data survives `make down && make up`
- [ ] `.env.example` lists the emulator variables

## Tasks
- [ ] `infra/firebase/Dockerfile`, `firebase.json`, `.firebaserc`
- [ ] Add `firebase` service to `docker-compose.yml`
- [ ] Add `firebase-admin`, `google-cloud-firestore` to backend dependencies
- [ ] Run the session cookie check; update spec Open questions (and architecture Auth if needed)
- [ ] Makefile target: `firebase-reset`
- [ ] Update `.env.example`

## Out of scope
- `ArticleRepository` (Phase 3)
- Login flow and `POST /auth/session` (Phase 3 and 4)
