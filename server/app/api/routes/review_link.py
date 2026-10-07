from fastapi import APIRouter, Depends, Request

from app.api.auth import require_session
from app.api.schemas import ReviewLinkOut
from app.core.ports.article_repository import ArticleRepository
from app.core.ports.clock import Clock
from app.core.ports.secret_store import SecretStore
from app.core.use_cases.review_link import get_or_create_review_link, reset_review_link

router = APIRouter(dependencies=[Depends(require_session)])


def get_repository(request: Request) -> ArticleRepository:
    return request.app.state.container.article_repository


def get_secret_store(request: Request) -> SecretStore:
    return request.app.state.container.secret_store


def get_clock(request: Request) -> Clock:
    return request.app.state.container.clock


def get_web_base_url(request: Request) -> str:
    return request.app.state.container.web_base_url


@router.get("/review-link")
def get_review_link(
    repository: ArticleRepository = Depends(get_repository),
    secret_store: SecretStore = Depends(get_secret_store),
    clock: Clock = Depends(get_clock),
    web_base_url: str = Depends(get_web_base_url),
) -> ReviewLinkOut:
    url, created_at = get_or_create_review_link(repository, secret_store, clock, web_base_url)
    return ReviewLinkOut(url=url, created_at=created_at)


@router.post("/review-link/reset")
def reset_review_link_route(
    repository: ArticleRepository = Depends(get_repository),
    secret_store: SecretStore = Depends(get_secret_store),
    clock: Clock = Depends(get_clock),
    web_base_url: str = Depends(get_web_base_url),
) -> ReviewLinkOut:
    url, created_at = reset_review_link(repository, secret_store, clock, web_base_url)
    return ReviewLinkOut(url=url, created_at=created_at)
