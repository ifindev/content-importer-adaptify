# T-023 Fail fast on Firestore startup failure in GCP

**Phase:** 3 · API · **Status:** done · **Size:** S
**Refs:** architecture: GCP services, Local setup
**Depends on:** T-013
**Improves:** T-013

## Goal
In production, a broken Firestore connection at startup (bad IAM role, outage, wrong project) fails the deploy loudly instead of silently booting into a data-losing in-memory repository.

## Analysis

### Flow
1. `build_container` currently catches *any* exception from constructing `FirestoreArticleRepository` and falls back to `InMemoryArticleRepository`, logging an `ERROR` but letting the API boot and keep running — mirroring the WordPress-credentials-check leniency.
2. That's the right call locally (lets you work on unrelated things with the emulator down), but wrong in GCP: Cloud Run would report a healthy revision while every article write vanishes on the next restart, with only a log line as a signal.
3. Gate the fallback on `settings.app_env` (already `Literal["local", "gcp", "test"]`): fall back only for `local`/`test`; re-raise for `gcp`, so FastAPI's lifespan fails, the Cloud Run revision fails to come up, and the deploy is visibly broken.

### Edge cases
| Case | Behavior |
| --- | --- |
| Firestore unreachable, `app_env=local` or `test` | Falls back to in-memory, logs `ERROR`, API keeps running (today's behavior, unchanged) |
| Firestore unreachable, `app_env=gcp` | `build_container` re-raises; lifespan startup fails; Cloud Run revision fails to start, visible in Cloud Logging and the deploy status |

## Acceptance criteria
- [x] With `app_env=gcp` and Firestore construction raising, `build_container` propagates the error instead of falling back.
- [x] With `app_env=local` (default) or `app_env=test`, behavior is unchanged: falls back to `InMemoryArticleRepository`, logs an error, keeps running.
- [x] Unit test covers both branches.

## Tasks
- [x] `server/app/container.py`: gate the except-fallback in `build_container` by `settings.app_env`.
- [x] Unit test: construct with a Firestore client that raises, assert fallback for `local`/`test` and re-raise for `gcp`.

## Out of scope
- Cloud Run health checks, alerting, or retry/backoff logic — a hard failure on startup is Cloud Run's own signal to not route traffic to the broken revision; no extra infra needed.
