import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.auth import InvalidSessionError
from app.api.routes.articles import ArticleNotFoundError, EmptyUpdateError, PayloadTooLargeError
from app.api.routes.articles import router as articles_router
from app.api.routes.auth import router as auth_router
from app.api.routes.imports import NoFilesError, TooManyFilesError
from app.api.routes.imports import router as imports_router
from app.api.routes.review_link import router as review_link_router
from app.container import build_container
from app.core.domain.errors import (
    EmptyContentError,
    NotAwaitingApprovalError,
    NotEditableError,
    NotSendableError,
    WordPressError,
)
from app.settings import Settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    app.state.container = build_container(settings)
    app.state.container.article_repository.ensure_site_bootstrapped(
        settings.site_name, settings.wp_base_url
    )
    try:
        await app.state.container.publisher.check_credentials()
        logger.info("WordPress credentials OK")
    except WordPressError as exc:
        detail = (exc.message or str(exc)).rstrip(".")
        logger.error(
            "WordPress credential check failed (%s): check WP_BASE_URL, WP_USERNAME, and "
            "WP_APP_PASSWORD in .env — %s. The API will keep running.",
            exc.code,
            detail,
        )
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Content Importer API", lifespan=lifespan)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.exception_handler(InvalidSessionError)
    def invalid_session_handler(request: Request, exc: InvalidSessionError) -> JSONResponse:
        return JSONResponse(status_code=401, content={"code": "invalid_token"})

    @app.exception_handler(ArticleNotFoundError)
    def article_not_found_handler(request: Request, exc: ArticleNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"code": "not_found"})

    @app.exception_handler(EmptyContentError)
    def empty_content_handler(request: Request, exc: EmptyContentError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"code": "empty_content"})

    @app.exception_handler(PayloadTooLargeError)
    def payload_too_large_handler(request: Request, exc: PayloadTooLargeError) -> JSONResponse:
        return JSONResponse(status_code=413, content={"code": "payload_too_large"})

    @app.exception_handler(NoFilesError)
    def no_files_handler(request: Request, exc: NoFilesError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"code": "no_files"})

    @app.exception_handler(TooManyFilesError)
    def too_many_files_handler(request: Request, exc: TooManyFilesError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"code": "too_many_files"})

    @app.exception_handler(NotEditableError)
    def not_editable_handler(request: Request, exc: NotEditableError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"code": "not_editable"})

    @app.exception_handler(EmptyUpdateError)
    def empty_update_handler(request: Request, exc: EmptyUpdateError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"code": "empty_update"})

    @app.exception_handler(NotSendableError)
    def not_sendable_handler(request: Request, exc: NotSendableError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"code": "not_sendable"})

    @app.exception_handler(NotAwaitingApprovalError)
    def not_awaiting_approval_handler(
        request: Request, exc: NotAwaitingApprovalError
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"code": "not_awaiting_approval"})

    app.include_router(auth_router)
    app.include_router(articles_router)
    app.include_router(imports_router)
    app.include_router(review_link_router)

    return app


app = create_app()
