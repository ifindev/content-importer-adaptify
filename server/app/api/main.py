import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.container import build_container
from app.core.domain.errors import WordPressError
from app.settings import Settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.container = build_container(Settings())
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

    return app


app = create_app()
