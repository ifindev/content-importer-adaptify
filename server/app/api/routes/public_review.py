import hmac

from fastapi import APIRouter, Depends, Request

from app.api.deps import (
    SiteContext,
    get_clock,
    get_internal_api_secret,
    get_public_site_context,
    get_sync_cache,
)
from app.api.rate_limit import check_rate_limit
from app.api.schemas.public_review import (
    ApproveRequest,
    ArticleCard,
    RequestChangesRequest,
    ReviewActionOut,
    ReviewArticleOut,
    ReviewPageOut,
)
from app.api.tags import CLIENT_REVIEW
from app.core.domain.statuses import Status
from app.core.ports.clock import Clock
from app.core.use_cases.review import (
    approve,
    get_review_article,
    get_review_page,
    request_changes,
)
from app.core.use_cases.sync_status import SyncCache, sync_statuses


def _client_ip(request: Request, secret: str) -> str:
    """The client's IP as the web app reports it. Only the web app holds the
    secret, so anyone else (a spoofed X-Forwarded-For included) is keyed by
    the address actually connecting."""
    claimed = request.headers.get("x-client-ip")
    sent = request.headers.get("x-internal-secret", "")
    if secret and claimed and hmac.compare_digest(sent.encode(), secret.encode()):
        return claimed
    return request.client.host if request.client else "unknown"


def rate_limit_client(request: Request, secret: str = Depends(get_internal_api_secret)) -> None:
    """Router-level, so it runs before the token lookup: a flood of bad
    tokens is limited too, not just requests for a real link."""
    check_rate_limit(_client_ip(request, secret))


router = APIRouter(tags=[CLIENT_REVIEW], dependencies=[Depends(rate_limit_client)])


@router.get("/review/{token}")
async def get_review(
    token: str,
    ctx: SiteContext = Depends(get_public_site_context),
    clock: Clock = Depends(get_clock),
    cache: SyncCache = Depends(get_sync_cache),
) -> ReviewPageOut:
    result = await sync_statuses(ctx.repository, ctx.publisher, clock, cache, site_id=ctx.site_id)
    site, groups = get_review_page(ctx.repository, token)
    return ReviewPageOut(
        site_name=site.name,
        waiting=[ArticleCard(**a.model_dump()) for a in groups[Status.AWAITING_APPROVAL]],
        upcoming=[ArticleCard(**a.model_dump()) for a in groups[Status.SCHEDULED]],
        published=[ArticleCard(**a.model_dump()) for a in groups[Status.PUBLISHED]],
        wordpress_unreachable=result.unreachable,
    )


@router.get("/review/{token}/articles/{article_id}")
def get_review_article_route(
    token: str,
    article_id: str,
    ctx: SiteContext = Depends(get_public_site_context),
) -> ReviewArticleOut:
    article = get_review_article(ctx.repository, token, article_id)
    return ReviewArticleOut(**article.model_dump())


@router.post("/review/{token}/articles/{article_id}/approve")
def approve_route(
    token: str,
    article_id: str,
    body: ApproveRequest,
    ctx: SiteContext = Depends(get_public_site_context),
    clock: Clock = Depends(get_clock),
) -> ReviewActionOut:
    article = approve(ctx.repository, clock, token, article_id, body.client_name, body.version)
    return ReviewActionOut(id=article.id, status=article.status)


@router.post("/review/{token}/articles/{article_id}/request-changes")
def request_changes_route(
    token: str,
    article_id: str,
    body: RequestChangesRequest,
    ctx: SiteContext = Depends(get_public_site_context),
    clock: Clock = Depends(get_clock),
) -> ReviewActionOut:
    article = request_changes(
        ctx.repository, clock, token, article_id, body.client_name, body.comment, body.version
    )
    return ReviewActionOut(id=article.id, status=article.status)
