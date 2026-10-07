from fastapi import APIRouter, Depends, Query, Request

from app.api.auth import require_session
from app.api.schemas import ArticleDetail, ArticleSummary, EventOut
from app.core.domain.statuses import Status
from app.core.ports.article_repository import ArticleRepository
from app.core.ports.clock import Clock
from app.core.ports.document_parser import DocumentParser

router = APIRouter(dependencies=[Depends(require_session)])


class ArticleNotFoundError(Exception):
    pass


class PayloadTooLargeError(Exception):
    pass


def get_repository(request: Request) -> ArticleRepository:
    return request.app.state.container.article_repository


def get_document_parser(request: Request) -> DocumentParser:
    return request.app.state.container.document_parser


def get_clock(request: Request) -> Clock:
    return request.app.state.container.clock


@router.get("/articles")
def list_articles(
    status: Status | None = Query(None),
    repository: ArticleRepository = Depends(get_repository),
) -> dict[str, list[ArticleSummary]]:
    articles = repository.list_articles(status=status)
    return {"articles": [ArticleSummary(**a.model_dump()) for a in articles]}


@router.get("/articles/{article_id}")
def get_article(
    article_id: str,
    repository: ArticleRepository = Depends(get_repository),
) -> ArticleDetail:
    article = repository.get_article(article_id)
    if article is None:
        raise ArticleNotFoundError
    events = repository.list_events(article_id)
    return ArticleDetail(
        **article.model_dump(), events=[EventOut(**e.model_dump()) for e in events]
    )
