from fastapi import APIRouter, Depends, Request

from app.api.rate_limit import check_rate_limit
from app.api.schemas import ArticleCard, ReviewArticleOut, ReviewPageOut
from app.core.domain.statuses import Status
from app.core.ports.article_repository import ArticleRepository
from app.core.use_cases.review import get_review_article, get_review_page

router = APIRouter()


def get_repository(request: Request) -> ArticleRepository:
    return request.app.state.container.article_repository


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded
    return request.client.host if request.client else "unknown"


@router.get("/review/{token}")
def get_review(
    token: str,
    request: Request,
    repository: ArticleRepository = Depends(get_repository),
) -> ReviewPageOut:
    check_rate_limit(_client_ip(request))
    site, groups = get_review_page(repository, token)
    return ReviewPageOut(
        site_name=site.name,
        waiting=[ArticleCard(**a.model_dump()) for a in groups[Status.AWAITING_APPROVAL]],
        upcoming=[ArticleCard(**a.model_dump()) for a in groups[Status.SCHEDULED]],
        published=[ArticleCard(**a.model_dump()) for a in groups[Status.PUBLISHED]],
    )


@router.get("/review/{token}/articles/{article_id}")
def get_review_article_route(
    token: str,
    article_id: str,
    request: Request,
    repository: ArticleRepository = Depends(get_repository),
) -> ReviewArticleOut:
    check_rate_limit(_client_ip(request))
    article = get_review_article(repository, token, article_id)
    return ReviewArticleOut(**article.model_dump())
