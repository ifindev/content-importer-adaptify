# T-024 Consolidate API exception handling

**Phase:** 3 · API · **Status:** analyzed · **Size:** S
**Refs:** architecture: Server folder layout (adds the api/error_handlers.py, api/http_errors.py convention)

## Goal
`main.py` currently repeats the same exception-handler decorator 17 times, and the exception classes behind them are scattered across three different layers. After this ticket, `main.py` wires exception handling in one line, and every exception class lives in exactly one of two clear homes based on where it's raised.

## Analysis

### Current state
Grepping every `class .*(Exception)` in `server/app/` turns up 19 classes that split cleanly into four groups:
- **Already correct** (`core/domain/errors.py`): `WordPressError`, `NotAllowed` (never gets a handler — a safety net that should never surface, since every use case pre-checks status before calling `lifecycle.transition`), `NotEditableError`, `EmptyContentError`, `NotSendableError`, `NotAwaitingApprovalError`, `ArticleChangedError`, `NotSchedulableError`, `NotFailedError`, `PublishAtInPastError`.
- **Misplaced use-case errors**, move into `core/domain/errors.py`: `InvalidTokenError`, `ArticleNotVisibleError` (currently in `core/use_cases/review.py`, raised from use-case code just like all the others above — the only two that broke the pattern).
- **Ad hoc API/route-validation errors**, move into a new `api/http_errors.py`: `ArticleNotFoundError`, `EmptyUpdateError`, `PayloadTooLargeError` (from `api/routes/articles.py`), `NoFilesError`, `TooManyFilesError` (from `api/routes/imports.py`, which also cross-imports `PayloadTooLargeError` from `articles.py` today).
- **Already correctly colocated, leave alone**: `InvalidSessionError` (`api/auth.py`), `RateLimitedError` (`api/rate_limit.py`) — each defined and raised in the same single-purpose module.

`main.py` has 17 near-identical `@app.exception_handler(X)` blocks, each just `JSONResponse(status_code=N, content={"code": "..."})`, plus one (`WordPressError`) whose body also includes `message`.

### Design
- New `server/app/api/error_handlers.py`: a `(exception_class, status_code, code)` table plus one generic handler factory, registered via `app.add_exception_handler(...)` in a loop. `WordPressError` is handled as a one-off (its body also includes `message`). Exposes `register_exception_handlers(app: FastAPI) -> None`.
- `main.py` calls `register_exception_handlers(app)` once in `create_app()`. It keeps its own `WordPressError` import because `lifespan()` separately catches it for the startup credentials check — unrelated to this refactor.
- `core/domain/errors.py` gains `InvalidTokenError`, `ArticleNotVisibleError`.
- New `api/http_errors.py` gains `ArticleNotFoundError`, `EmptyUpdateError`, `PayloadTooLargeError`, `NoFilesError`, `TooManyFilesError`.

### Decisions
- Named `api/http_errors.py`, not `api/errors.py` — `core/domain/errors.py` already owns that bare name one layer down; a same-named file at the API layer would be confusing to import correctly.
- `docs/architecture.md`'s folder layout is updated in this same change (no prior convention existed for where handler registration lives).

## Acceptance criteria
- [ ] `main.py` has zero `@app.exception_handler` decorators; `create_app()` calls one `register_exception_handlers(app)`.
- [ ] Every handler-mapped exception class lives in `core/domain/errors.py`, `api/http_errors.py`, or its own small infra module (`api/auth.py`, `api/rate_limit.py`) — nowhere else.
- [ ] Every status-code/`code` mapping is byte-for-byte unchanged — the existing test suite passes with only import-path updates, no assertion changes.
- [ ] `docs/architecture.md` folder layout shows the two new files.

## Tasks
- [ ] `core/domain/errors.py`: add `InvalidTokenError`, `ArticleNotVisibleError`.
- [ ] `core/use_cases/review.py`: remove the two class defs, import from `core.domain.errors`.
- [ ] `api/http_errors.py` (new): the five moved API-validation errors.
- [ ] `api/routes/articles.py`, `api/routes/imports.py`: remove ad hoc class defs, import from `api/http_errors.py` (drop `imports.py`'s cross-import from `articles.py`).
- [ ] `api/error_handlers.py` (new): table-driven `register_exception_handlers(app)`.
- [ ] `api/main.py`: delete the 17 decorator blocks and now-unneeded imports; call `register_exception_handlers(app)`.
- [ ] Update `tests/unit/test_review_actions.py` and `tests/unit/test_review_page.py`'s imports for the two moved classes.
- [ ] `docs/architecture.md`: add the two new files to the folder layout tree.
- [ ] Run the full unit + integration suite — must pass unmodified in assertions.

## Out of scope
- Any change to a status code, error `code` string, or response body shape.
- Relocating `InvalidSessionError`/`RateLimitedError` — already correctly colocated with their one raise site.
- T-021/T-022 (status sync, agency report) — unrelated, untouched.
