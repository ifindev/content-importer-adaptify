from fastapi import APIRouter, Depends, Query, Request

from app.api.auth import require_session
from app.api.schemas import ArticleDetail, ArticleSummary, ArticleUpdate, EventOut
from app.core.domain.statuses import Status
from app.core.ports.article_repository import ArticleRepository
from app.core.ports.clock import Clock
from app.core.ports.document_parser import DocumentParser
from app.core.use_cases.edit_article import edit_article
from app.core.use_cases.review import pull_back, send_for_review

router = APIRouter(dependencies=[Depends(require_session)])

PATCH_BODY_MAX_BYTES = 2 * 1024 * 1024


class ArticleNotFoundError(Exception):
    pass


class EmptyUpdateError(Exception):
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


@router.patch("/articles/{article_id}")
def update_article(
    article_id: str,
    body: ArticleUpdate,
    repository: ArticleRepository = Depends(get_repository),
    parser: DocumentParser = Depends(get_document_parser),
    clock: Clock = Depends(get_clock),
    uid: str = Depends(require_session),
) -> ArticleDetail:
    if body.title is None and body.slug is None and body.body_html is None:
        raise EmptyUpdateError
    if body.body_html is not None and len(body.body_html.encode()) > PATCH_BODY_MAX_BYTES:
        raise PayloadTooLargeError

    article = repository.get_article(article_id)
    if article is None:
        raise ArticleNotFoundError

    updated = edit_article(
        article, body.title, body.slug, body.body_html, repository, parser, clock, actor=uid
    )
    events = repository.list_events(article_id)
    return ArticleDetail(
        **updated.model_dump(), events=[EventOut(**e.model_dump()) for e in events]
    )


@router.post("/articles/{article_id}/send-for-review")
def send_for_review_route(
    article_id: str,
    repository: ArticleRepository = Depends(get_repository),
    clock: Clock = Depends(get_clock),
    uid: str = Depends(require_session),
) -> ArticleDetail:
    article = repository.get_article(article_id)
    if article is None:
        raise ArticleNotFoundError

    updated = send_for_review(article, repository, clock, actor=uid)
    events = repository.list_events(article_id)
    return ArticleDetail(
        **updated.model_dump(), events=[EventOut(**e.model_dump()) for e in events]
    )


@router.post("/articles/{article_id}/pull-back")
def pull_back_route(
    article_id: str,
    repository: ArticleRepository = Depends(get_repository),
    clock: Clock = Depends(get_clock),
    uid: str = Depends(require_session),
) -> ArticleDetail:
    article = repository.get_article(article_id)
    if article is None:
        raise ArticleNotFoundError

    updated = pull_back(article, repository, clock, actor=uid)
    events = repository.list_events(article_id)
    return ArticleDetail(
        **updated.model_dump(), events=[EventOut(**e.model_dump()) for e in events]
    )
