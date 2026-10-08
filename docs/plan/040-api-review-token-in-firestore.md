# T-040 Review token encrypted in Firestore

**Phase:** 5 · API · **Status:** analyzed · **Size:** S
**Refs:** R3.1, R3.2, R3.7; spec: Data model, API endpoints (review-token Decision); architecture: GCP services
**Depends on:** —
**Improves:** T-016, T-031

## Goal
Review links survive restarts and work on every Cloud Run instance. The agency can copy the same link tomorrow that the client got today.

## Analysis

### Problem
`LocalFileSecretStore` (`server/app/adapters/secret_store.py`) keeps the plaintext review token in `server/.secrets.local.json`. On Cloud Run that file sits on the container's temporary disk:
- it is lost on every restart and redeploy;
- each instance has its own copy.

When the token is missing, `get_or_create_review_link` (`core/use_cases/review_link.py:16-18`) silently rotates it. The agency gets a new link, and every link a client already has stops working.

The secret store is only used to show the link again. Client requests are checked by hash: `api/deps.py:39-43` → `find_site_id_by_review_token_hash` (a Firestore `where`), then `hmac.compare_digest` in `core/use_cases/review.py:22`.

### Approach
Store the token encrypted on the site document, with the same cipher and key as the WordPress app password (`CREDENTIAL_ENCRYPTION_KEY`). A database export alone still can't open a review link, which was the point of the original decision. It removes a port, two adapters and a local file, and needs no Secret Manager IAM or per-version cost.

### Data changes
- `sites` gains `review_token_encrypted` (Fernet ciphertext, string).
- `review_token_hash` and `review_token_created_at` stay: the hash is still the lookup key.
- The plaintext token never touches Firestore.

### Core
- Reuse the `CredentialCipher` port (`core/ports/credential_cipher.py`). The use cases that touch the token get the cipher the way `create_site` already does for the app password.
- `create_site.py:41`: set `review_token_encrypted = cipher.encrypt(token)` on the new site, next to the hash (line 35), instead of calling `set_review_token`.
- `review_link.py`:
  - `get_or_create_review_link`: decrypt `review_token_encrypted`. If the field is missing, or `decrypt` returns `""` (wrong key, see `FernetCredentialCipher.decrypt`), rotate, as it does today when the store returns `None`.
  - `_rotate` (lines 35-44): save hash, encrypted token and `created_at` to the site in one repository write. Drop the `set_review_token` call.
  - `reset_review_link` (lines 24-32): unchanged apart from `_rotate`.
- `Container.delete_site` (`container.py:61`): remove the `delete_review_token` call. The token is deleted with the site document.

### Deletions
- `core/ports/secret_store.py` (the `SecretStore` port).
- `adapters/secret_store.py` (`LocalFileSecretStore`) and `adapters/testing/secret_store.py` (`InMemorySecretStore`).
- In `container.py`: `SECRET_STORE_PATH` (line 29), the `secret_store` field (line 38) and its wiring (line 110).
- `.gitignore:19` (`server/.secrets.local.json`), and the local file itself if present.
- `.env.example:41-44` comment about the local secret store and Secret Manager.
- Any import-linter contract or test fixture that names the port.

### Small fix
`FernetCredentialCipher.decrypt` logs "Stored app password doesn't decrypt with the current key". It now decrypts tokens too, so make it "Stored secret doesn't decrypt with the current key", and update its docstring.

### Edge cases
| Case | Behavior |
| --- | --- |
| Existing local sites (token in the JSON file, no `review_token_encrypted`) | The first `GET /sites/{id}/review-link` rotates once. Local links change once. Local only, acceptable. |
| `CREDENTIAL_ENCRYPTION_KEY` changes | Decrypt returns `""`, so the next `GET review-link` rotates. Old client links stop working, and WordPress passwords also stop decrypting. Same failure mode as today's passwords; documented in architecture. |
| Reset link | New hash and new encrypted token in one write. The old link returns 404. |
| Delete site | The document goes, and the token with it. Nothing else to clean up. |
| Two instances read the link at the same time | Both decrypt the same stored token. No rotation, no race. |

### Decisions
- Reverses the spec's "the plaintext lives in the local secret store / Secret Manager". Update in this change:
  - spec R3.1: "Firestore stores a hash of the token for lookup and the token itself encrypted with the credential key, like the WordPress app password."
  - spec Data model, `sites` row: add `review_token_encrypted`; replace "the plaintext review token still never touches Firestore".
  - spec review-token Decision (spec.md:505): rewrite. Keep the reason (a database export can't open a review page) and say it now holds because the token is encrypted with a key that lives outside Firestore.
  - architecture GCP services, Secret Manager row: `CREDENTIAL_ENCRYPTION_KEY` encrypts WordPress app passwords **and review tokens**.
  - architecture "What Terraform creates", Secrets line: same.
  - architecture Local setup: remove any mention of `.secrets.local.json`.

## Acceptance criteria
- [ ] Unit tests, with the in-memory site repository and a real `FernetCredentialCipher`:
  - [ ] Create site stores `review_token_encrypted`, which decrypts to the token in the URL `GET review-link` returns.
  - [ ] `GET review-link` twice returns the same URL.
  - [ ] Reset returns a new URL, and the old token no longer resolves to the site.
  - [ ] A token encrypted under another key causes one rotation, then stays stable.
  - [ ] A site without `review_token_encrypted` (older data) gets one on the first `GET review-link`.
- [ ] Integration test (Firestore emulator): after create and after reset, the stored site document contains no plaintext token, only the hash and the ciphertext.
- [ ] `grep -rn "secret_store\|SecretStore\|secrets.local" server/ .env.example .gitignore` returns nothing.
- [ ] `make lint test` and `make test-integration` green.
- [ ] `openapi.json` unchanged (the API shape doesn't change). If it does change, run `make gen-api`.
- [ ] Local by hand: create a site, copy the link, restart the API container, copy again: same link, and it opens.
- [ ] spec.md and architecture.md updated as listed in Decisions.

## Tasks
- [ ] Write the unit tests above first (they fail).
- [ ] Add `review_token_encrypted` to the `Site` model and the Firestore mapping.
- [ ] Pass the cipher to `create_site` and the review-link use cases; encrypt on create and rotate; decrypt on get.
- [ ] Remove the `SecretStore` port, both adapters, the container wiring and `delete_review_token` from `delete_site`.
- [ ] Generalize the cipher's warning text.
- [ ] Clean `.gitignore` and `.env.example`.
- [ ] Integration test for "no plaintext in Firestore".
- [ ] Update spec.md and architecture.md.

## Out of scope
- Secret Manager for review tokens.
- Key rotation tooling for `CREDENTIAL_ENCRYPTION_KEY` (re-encrypting stored values under a new key).
