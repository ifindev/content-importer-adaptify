from fastapi import APIRouter, Depends, Query, Response

from app.api.auth import require_session
from app.api.deps import (
    SiteContext,
    get_clock,
    get_document_parser,
    get_site_context,
    get_sync_cache,
)
from app.api.http_errors import ArticleNotFoundError, EmptyUpdateError, PayloadTooLargeError
from app.api.schemas.articles import (
    ArticleDetail,
    ArticlesOut,
    ArticleSummary,
    ArticleUpdate,
    EventOut,
    ScheduleRequest,
)
from app.api.tags import ARTICLES, PUBLISHING
from app.core.domain.statuses import Status
from app.core.ports.clock import Clock
from app.core.ports.document_parser import DocumentParser
from app.core.use_cases.delete_article import delete_article
from app.core.use_cases.edit_article import edit_article
from app.core.use_cases.review import pull_back, send_for_review
from app.core.use_cases.schedule import retry, schedule
from app.core.use_cases.sync_status import SyncCache, sync_statuses

router = APIRouter(dependencies=[Depends(require_session)])

PATCH_BODY_MAX_BYTES = 2 * 1024 * 1024


@router.get("/articles", tags=[ARTICLES])
async def list_articles(
    status: Status | None = Query(None),
    ctx: SiteContext = Depends(get_site_context),
    clock: Clock = Depends(get_clock),
    cache: SyncCache = Depends(get_sync_cache),
) -> ArticlesOut:
    result = await sync_statuses(ctx.repository, ctx.publisher, clock, cache)
    articles = ctx.repository.list_articles(status=status)
    return ArticlesOut(
        articles=[ArticleSummary(**a.model_dump()) for a in articles],
        wordpress_unreachable=result.unreachable,
    )


@router.get("/articles/{article_id}", tags=[ARTICLES])
def get_article(
    article_id: str,
    ctx: SiteContext = Depends(get_site_context),
) -> ArticleDetail:
    article = ctx.repository.get_article(article_id)
    if article is None:
        raise ArticleNotFoundError
    events = ctx.repository.list_events(article_id)
    return ArticleDetail(
        **article.model_dump(), events=[EventOut(**e.model_dump()) for e in events]
    )


@router.patch("/articles/{article_id}", tags=[ARTICLES])
async def update_article(
    article_id: str,
    body: ArticleUpdate,
    ctx: SiteContext = Depends(get_site_context),
    parser: DocumentParser = Depends(get_document_parser),
    clock: Clock = Depends(get_clock),
    uid: str = Depends(require_session),
) -> ArticleDetail:
    if body.title is None and body.slug is None and body.body_html is None:
        raise EmptyUpdateError
    if body.body_html is not None and len(body.body_html.encode()) > PATCH_BODY_MAX_BYTES:
        raise PayloadTooLargeError

    article = ctx.repository.get_article(article_id)
    if article is None:
        raise ArticleNotFoundError

    updated = await edit_article(
        article,
        body.title,
        body.slug,
        body.body_html,
        ctx.repository,
        parser,
        clock,
        ctx.publisher,
        actor=uid,
    )
    events = ctx.repository.list_events(article_id)
    return ArticleDetail(
        **updated.model_dump(), events=[EventOut(**e.model_dump()) for e in events]
    )


@router.post("/articles/{article_id}/send-for-review", tags=[PUBLISHING])
def send_for_review_route(
    article_id: str,
    ctx: SiteContext = Depends(get_site_context),
    clock: Clock = Depends(get_clock),
    uid: str = Depends(require_session),
) -> ArticleDetail:
    article = ctx.repository.get_article(article_id)
    if article is None:
        raise ArticleNotFoundError

    updated = send_for_review(article, ctx.repository, clock, actor=uid)
    events = ctx.repository.list_events(article_id)
    return ArticleDetail(
        **updated.model_dump(), events=[EventOut(**e.model_dump()) for e in events]
    )


@router.post("/articles/{article_id}/pull-back", tags=[PUBLISHING])
def pull_back_route(
    article_id: str,
    ctx: SiteContext = Depends(get_site_context),
    clock: Clock = Depends(get_clock),
    uid: str = Depends(require_session),
) -> ArticleDetail:
    article = ctx.repository.get_article(article_id)
    if article is None:
        raise ArticleNotFoundError

    updated = pull_back(article, ctx.repository, clock, actor=uid)
    events = ctx.repository.list_events(article_id)
    return ArticleDetail(
        **updated.model_dump(), events=[EventOut(**e.model_dump()) for e in events]
    )


@router.post("/articles/{article_id}/schedule", tags=[PUBLISHING])
async def schedule_route(
    article_id: str,
    body: ScheduleRequest,
    ctx: SiteContext = Depends(get_site_context),
    clock: Clock = Depends(get_clock),
    uid: str = Depends(require_session),
) -> ArticleDetail:
    article = ctx.repository.get_article(article_id)
    if article is None:
        raise ArticleNotFoundError

    updated = await schedule(
        article, body.publish_at, ctx.repository, ctx.publisher, clock, actor=uid
    )
    events = ctx.repository.list_events(article_id)
    return ArticleDetail(
        **updated.model_dump(), events=[EventOut(**e.model_dump()) for e in events]
    )


@router.post("/articles/{article_id}/retry", tags=[PUBLISHING])
async def retry_route(
    article_id: str,
    ctx: SiteContext = Depends(get_site_context),
    clock: Clock = Depends(get_clock),
    uid: str = Depends(require_session),
) -> ArticleDetail:
    article = ctx.repository.get_article(article_id)
    if article is None:
        raise ArticleNotFoundError

    updated = await retry(article, ctx.repository, ctx.publisher, clock, actor=uid)
    events = ctx.repository.list_events(article_id)
    return ArticleDetail(
        **updated.model_dump(), events=[EventOut(**e.model_dump()) for e in events]
    )


@router.delete("/articles/{article_id}", status_code=204, tags=[ARTICLES])
def delete_article_route(
    article_id: str,
    ctx: SiteContext = Depends(get_site_context),
) -> Response:
    article = ctx.repository.get_article(article_id)
    if article is None:
        raise ArticleNotFoundError

    delete_article(article, ctx.repository)
    return Response(status_code=204)
