# T-016 Review link

**Phase:** 3 · API · **Status:** done · **Size:** S
**Refs:** R3.1, R3.2, R3.7, spec: Data model, Review link
**Depends on:** T-013

## Goal
The agency can get the site's review link to share with the client, and reset it if it leaks — the client-facing routes built in T-018/T-019 depend on this token existing.

## Analysis

### Flow
1. `GET /review-link` returns the current review URL, built from a configured web base URL + the **plaintext** token — but the plaintext token only exists at creation time (R3.1: "the app stores only a hash"). So the token must be cached somewhere the agency can still retrieve it, or the endpoint can only return it once.
2. Resolution (see Decisions): the plaintext token is generated once at first site bootstrap (T-013) or first call to this endpoint if still empty, returned, and from then on `GET /review-link` returns the same URL built from the stored hash's... — hashes aren't reversible, so the route **cannot** reconstruct the plaintext after the fact. The decision below settles this.

### API
`GET /review-link`

| Case | Status | Body |
| --- | --- | --- |
| OK | 200 | `{url: string, created_at: datetime}` |

`POST /review-link/reset`

| Case | Status | Body |
| --- | --- | --- |
| OK | 200 | `{url: string, created_at: datetime}` |

### Data changes
No new fields — `review_token_hash`, `review_token_created_at` already on `Site` (T-013).

### Core
- `core/lib/tokens.py`: `generate_token() -> str` (`secrets.token_urlsafe(32)`), `hash_token(token) -> str` (SHA-256 hex).
- `core/use_cases/review_link.py`: `get_or_create_review_link()`, `reset_review_link()`. Both return the **plaintext** token/URL — the use case is the only place that ever sees it, right at generation time.
- `core/ports/article_repository.py`: add `save_site(site)` if not already covered by T-013's repository surface.

### Decisions
- **The plaintext token is never persisted, so it can only be shown once per generation.** `GET /review-link` does **not** return a fresh, reconstructible URL on every call — it returns the URL generated the *first* time a link existed, cached in memory for the life of the process... which doesn't survive a restart and breaks the "copy the link" UI (R3.2) on any later visit. Instead: **the site bootstrap in T-013 is changed to generate the token immediately** (not left empty), and `GET /review-link` is redefined as "copy the review link" meaning *re-display the same link*, which requires the plaintext to be retrievable. **Final decision:** store the token in Secret Manager / local config alongside the WordPress credentials (same trust tier: a secret, not app data), keyed by site. Firestore keeps only the hash, used to verify incoming client requests (R3.1's actual requirement — "a leaked database export can't open the review page" — still holds, since the export is Firestore, not Secret Manager). `GET /review-link` reads the plaintext from Secret Manager/config and the hash check in T-018 reads Firestore. This is a deviation from a literal reading of R3.1 and must be reflected in `spec.md`'s Data model and R3.1 wording before this ticket is marked done.
- Locally, "Secret Manager" is a local env var / `.env` entry (same pattern as WordPress credentials in `settings.py`), not the Firestore emulator.

### Edge cases
| Case | Behavior |
| --- | --- |
| `GET /review-link` before any token exists (fresh install) | Generates one on first call, same as reset, logs an event |
| Reset while articles are Awaiting approval under the old link | Old token's hash no longer matches anything — those articles stay in their status; the client simply can't reach them until shared the new link (matches spec: reset "turns off the old one") |

## Acceptance criteria
- [x] `GET /review-link` returns a usable URL on a fresh site, generating a token if none exists.
- [x] `POST /review-link/reset` returns a new URL; the old token's hash no longer validates (verified once T-018 exists, cross-referenced there).
- [x] The plaintext token is never written to Firestore, only its SHA-256 hash.
- [x] `spec.md`'s Data model / R3.1 note updated to describe where the plaintext lives.
- [x] Swagger and Postman updated.

## Tasks
- [x] `core/lib/tokens.py`.
- [x] `core/use_cases/review_link.py`.
- [x] `api/routes/review_link.py`: `GET /review-link`, `POST /review-link/reset`.
- [x] Add the token's plaintext storage location to `settings.py`/`.env.example` (local) and note the Secret Manager entry for deploy (T-0xx deploy ticket, Phase 5, picks this up).
- [x] Update `spec.md` (Data model, R3.1).
- [x] Unit tests: token generation/hashing, reset invalidates old hash.
- [x] Integration test: Firestore emulator for the hash side.
- [x] `pnpm gen:api`.

## Out of scope
- Per-site on/off switch or passcode (spec's noted possible next steps).
- The client-facing token check itself (T-018).
