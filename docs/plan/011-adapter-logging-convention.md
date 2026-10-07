# T-011 Adapter request/response logging convention

**Phase:** 2 · Local infra · **Status:** done · **Size:** S
**Refs:** architecture: Server (Logging)

## Goal
Every external API adapter call logs enough request/response detail (ids, statuses — not full bodies) to trace what happened, as a documented convention future adapters follow.

## Analysis
`WordPressPublisher._request` already logged method/path/status for every call, but `create_scheduled` and `get_statuses` discarded the response content after extracting what they needed — so a passing (or failing) run showed that a call succeeded, not what it actually did (which post id, which statuses). This was found by inspecting `make test-integration` output after log visibility was turned on (pytest's `--log-cli-level=INFO`), which is a separate, already-fixed gap (log output wasn't shown at all before).

### Decisions
- The convention goes in `docs/architecture.md` under `## Server`, not `CLAUDE.md` — `CLAUDE.md` only points there, matching how it already points to `docs/architecture.md` for the import-linter rule.
- No shared logging port/helper yet: `WordPressPublisher` is still the only external adapter. Add one when a second adapter (Vertex AI, P2) needs the same pattern.
- Log identifying fields (ids, slugs, statuses), never full payloads — `WordPressPublisher` sends full article HTML, which doesn't belong in logs.

## Acceptance criteria
- [x] `docs/architecture.md` has a Logging subsection describing the convention.
- [x] `CLAUDE.md` points to it.
- [x] `WordPressPublisher.create_scheduled` and `get_statuses` log their request/response identifying fields, not just status.
- [x] `make test-integration` output shows, for the publish flow, which post id was created and what statuses were returned, without dumping the full article HTML.

## Tasks
- [x] Write the Logging subsection in `docs/architecture.md`.
- [x] Add the one-line pointer in `CLAUDE.md`.
- [x] Update `publisher.py` call sites.
- [x] Run `make test-integration`, confirm the new log lines appear.

## Out of scope
- A shared logger port/abstraction in `core/`.
- Structured/JSON logging.
- Logging for adapters that don't exist yet (Firestore, Vertex AI).
- Log level configuration via env var.
