from fastapi import APIRouter, Depends

from app.api.auth import require_session
from app.api.deps import (
    SiteContext,
    get_clock,
    get_secret_store,
    get_site_context,
    get_web_base_url,
)
from app.api.schemas.review_link import ReviewLinkOut
from app.api.tags import REVIEW_LINK
from app.core.ports.clock import Clock
from app.core.ports.secret_store import SecretStore
from app.core.use_cases.review_link import get_or_create_review_link, reset_review_link

router = APIRouter(tags=[REVIEW_LINK], dependencies=[Depends(require_session)])


@router.get("/review-link")
def get_review_link(
    ctx: SiteContext = Depends(get_site_context),
    secret_store: SecretStore = Depends(get_secret_store),
    clock: Clock = Depends(get_clock),
    web_base_url: str = Depends(get_web_base_url),
) -> ReviewLinkOut:
    url, created_at = get_or_create_review_link(
        ctx.site_id, ctx.repository, secret_store, clock, web_base_url
    )
    return ReviewLinkOut(url=url, created_at=created_at)


@router.post("/review-link/reset")
def reset_review_link_route(
    ctx: SiteContext = Depends(get_site_context),
    secret_store: SecretStore = Depends(get_secret_store),
    clock: Clock = Depends(get_clock),
    web_base_url: str = Depends(get_web_base_url),
) -> ReviewLinkOut:
    url, created_at = reset_review_link(
        ctx.site_id, ctx.repository, secret_store, clock, web_base_url
    )
    return ReviewLinkOut(url=url, created_at=created_at)
