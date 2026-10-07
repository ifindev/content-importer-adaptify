import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.error_handlers import register_exception_handlers
from app.api.routes.articles import router as articles_router
from app.api.routes.auth import router as auth_router
from app.api.routes.imports import router as imports_router
from app.api.routes.public_review import router as public_review_router
from app.api.routes.report import router as report_router
from app.api.routes.review_link import router as review_link_router
from app.api.routes.sites import router as sites_router
from app.api.tags import HEALTH, OPENAPI_TAGS
from app.container import build_container
from app.settings import Settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    app.state.container = build_container(settings)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Content Importer API", lifespan=lifespan, openapi_tags=OPENAPI_TAGS)

    @app.get("/health", tags=[HEALTH])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    register_exception_handlers(app)

    app.include_router(auth_router)
    app.include_router(sites_router)
    app.include_router(articles_router, prefix="/sites/{site_id}")
    app.include_router(imports_router, prefix="/sites/{site_id}")
    app.include_router(review_link_router, prefix="/sites/{site_id}")
    app.include_router(public_review_router)
    app.include_router(report_router, prefix="/sites/{site_id}")

    return app


app = create_app()
