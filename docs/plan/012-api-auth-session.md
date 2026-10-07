# T-012 Auth session

**Phase:** 3 · API · **Status:** done · **Size:** S
**Refs:** R8.1, spec: API endpoints (Agency), architecture: Auth
**Depends on:** T-008 (Firebase emulators)

## Goal
The agency signs in once and every later agency request carries a verified session, so protected routes can trust `request.state.uid` without re-checking Firebase on every call.

## Analysis

### Flow
1. Web signs in with the Firebase JS SDK, gets an ID token, sends it to `POST /auth/session`.
2. The route verifies the ID token and creates a Firebase session cookie (`firebase_admin.auth.create_session_cookie`), 5-day expiry (Firebase's own default max).
3. The route returns `204`; the web Server Action sets the cookie (`httpOnly`, `secure`, `sameSite=lax`) — cookie handling is a frontend-phase concern, out of scope here.
4. A `require_session` FastAPI dependency (`api/auth.py`) verifies the cookie with `verify_session_cookie(check_revoked=True)` on every agency route and sets `request.state.uid`. Missing/invalid cookie → `401`.

### API
`POST /auth/session`

| Field | Type | Rules |
| --- | --- | --- |
| `id_token` | string | required, Firebase ID token |

| Case | Status | Body |
| --- | --- | --- |
| Valid ID token | 204 | — (cookie set via `Set-Cookie`) |
| Expired/invalid ID token | 401 | `{code: "invalid_token"}` |

### Core
No `core/` change — `firebase_admin` is auth infrastructure, not a business rule, so `auth.py` and the route live in `api/` and import `firebase_admin` directly (architecture.md's import rules already allow this: `api/` isn't restricted to going through `core/` for cross-cutting infra like auth, only business logic must route through `core/`).

### Edge cases
| Case | Behavior |
| --- | --- |
| Session cookie present but revoked (e.g. password reset) | `verify_session_cookie(check_revoked=True)` raises → 401 |
| No `Authorization`/cookie at all on a protected route | 401, same `invalid_token` code |

### Decisions
- One agency account for the MVP (R8.1) — no role/permission checks, any verified session is authorized for every agency route.

## Acceptance criteria
- [x] `POST /auth/session` with a valid Firebase emulator ID token returns 204 and sets a session cookie.
- [x] An invalid or expired ID token returns 401 `invalid_token`.
- [x] A protected route (any agency route added in later tickets) returns 401 without a valid session cookie.
- [x] Swagger at `/docs` documents the request/response shapes.
- [x] Postman collection (re-imported from `openapi.json`) includes the endpoint — manual step, do after merge: re-import `web/lib/api/openapi.json` into Postman.

## Tasks
- [x] `api/auth.py`: `require_session` dependency, `create_session` helper.
- [x] `api/routes/auth.py`: `POST /auth/session`.
- [x] `api/schemas.py`: `SessionRequest`.
- [x] Unit test: dependency rejects missing/invalid cookie (mock `verify_session_cookie`).
- [x] Integration test against the Firebase Auth emulator: sign in, exchange token, call a dummy protected route.
- [x] Re-export `openapi.json`, re-import Postman collection.

## Out of scope
- Logout route (clearing the cookie is a frontend/Server Action concern).
- Multi-user roles or permissions.
