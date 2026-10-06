from fastapi import FastAPI

from app.container import build_container
from app.settings import Settings


def create_app() -> FastAPI:
    app = FastAPI(title="Content Importer API")
    app.state.container = build_container(Settings())

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
