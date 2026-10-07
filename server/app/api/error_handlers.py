from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.auth import InvalidSessionError
from app.api.http_errors import (
    ArticleNotFoundError,
    EmptyUpdateError,
    NoFilesError,
    PayloadTooLargeError,
    SiteNotFoundError,
    TooManyFilesError,
)
from app.api.rate_limit import RateLimitedError
from app.core.domain.errors import (
    ArticleChangedError,
    ArticleNotVisibleError,
    EmptyContentError,
    InvalidTokenError,
    NotAwaitingApprovalError,
    NotEditableError,
    NotFailedError,
    NotSchedulableError,
    NotSendableError,
    PublishAtInPastError,
    WordPressConnectionTestFailedError,
    WordPressError,
)

_SIMPLE_HANDLERS: tuple[tuple[type[Exception], int, str], ...] = (
    (InvalidSessionError, 401, "invalid_token"),
    (ArticleNotFoundError, 404, "not_found"),
    (InvalidTokenError, 404, "not_found"),
    (ArticleNotVisibleError, 404, "not_found"),
    (EmptyContentError, 422, "empty_content"),
    (PayloadTooLargeError, 413, "payload_too_large"),
    (NoFilesError, 422, "no_files"),
    (TooManyFilesError, 422, "too_many_files"),
    (NotEditableError, 409, "not_editable"),
    (EmptyUpdateError, 422, "empty_update"),
    (NotSendableError, 409, "not_sendable"),
    (NotAwaitingApprovalError, 409, "not_awaiting_approval"),
    (RateLimitedError, 429, "rate_limited"),
    (ArticleChangedError, 409, "article_changed"),
    (NotSchedulableError, 409, "not_schedulable"),
    (NotFailedError, 409, "not_failed"),
    (PublishAtInPastError, 422, "publish_at_in_past"),
    (SiteNotFoundError, 404, "site_not_found"),
)


def register_exception_handlers(app: FastAPI) -> None:
    for exc_class, status_code, code in _SIMPLE_HANDLERS:
        app.add_exception_handler(exc_class, _simple_handler(status_code, code))
    app.add_exception_handler(WordPressError, _wordpress_error_handler)
    app.add_exception_handler(
        WordPressConnectionTestFailedError, _wordpress_connection_test_failed_handler
    )


def _simple_handler(status_code: int, code: str):
    def handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=status_code, content={"code": code})

    return handler


def _wordpress_error_handler(request: Request, exc: WordPressError) -> JSONResponse:
    return JSONResponse(
        status_code=502,
        content={"code": "wordpress_error", "message": exc.message or str(exc)},
    )


def _wordpress_connection_test_failed_handler(
    request: Request, exc: WordPressConnectionTestFailedError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"code": "wp_connection_failed", "message": exc.message or str(exc)},
    )
