from fastapi import APIRouter, Depends, Response

from app.api.auth import require_session
from app.api.deps import get_clock, get_container
from app.api.http_errors import EmptyUpdateError, InsecureUrlError, SiteNotFoundError
from app.api.schemas.sites import (
    SiteConnectionTest,
    SiteCreate,
    SiteOut,
    SitesOut,
    SiteSummary,
    SiteUpdate,
)
from app.api.tags import SITES
from app.container import Container
from app.core.domain.errors import WordPressConnectionTestFailedError
from app.core.domain.models import Site
from app.core.domain.statuses import Status
from app.core.ports.clock import Clock
from app.core.use_cases.check_site_connection import check_site_connection
from app.core.use_cases.create_site import create_site
from app.core.use_cases.edit_site import edit_site

router = APIRouter(tags=[SITES], dependencies=[Depends(require_session)])

_OUT_FIELDS = set(SiteOut.model_fields)


def _out(site: Site) -> SiteOut:
    return SiteOut(**site.model_dump(include=_OUT_FIELDS))


def _get_site(site_id: str, container: Container) -> Site:
    site = container.site_repository.get_site(site_id)
    if site is None:
        raise SiteNotFoundError
    return site


def _require_https(url: str | None, container: Container) -> None:
    if url and not url.startswith("https://") and not container.allow_http_wordpress:
        raise InsecureUrlError


@router.post("/sites", status_code=201)
async def create_site_route(
    body: SiteCreate,
    container: Container = Depends(get_container),
    clock: Clock = Depends(get_clock),
) -> SiteOut:
    _require_https(body.wp_base_url, container)
    site = await create_site(
        body.name,
        body.wp_base_url,
        body.wp_username,
        body.wp_app_password,
        container.site_repository,
        container.credential_cipher,
        clock,
        container.build_publisher_from_credentials,
    )
    return _out(site)


@router.post("/sites/test-connection", status_code=204)
async def test_connection_route(
    body: SiteConnectionTest,
    container: Container = Depends(get_container),
) -> Response:
    _require_https(body.wp_base_url, container)
    await check_site_connection(
        body.wp_base_url,
        body.wp_username,
        body.wp_app_password,
        container.build_publisher_from_credentials,
    )
    return Response(status_code=204)


@router.post("/sites/{site_id}/test-connection", status_code=204)
async def test_site_connection_route(
    site_id: str,
    body: SiteUpdate | None = None,
    container: Container = Depends(get_container),
    clock: Clock = Depends(get_clock),
) -> Response:
    """Tests the stored credentials, with any fields in the body overriding
    them (the edit dialog, where an empty password means the stored one).
    Testing exactly what is stored records the result on the site."""
    site = _get_site(site_id, container)
    overrides = body or SiteUpdate()
    _require_https(overrides.wp_base_url, container)
    try:
        await check_site_connection(
            overrides.wp_base_url or site.wp_base_url,
            overrides.wp_username or site.wp_username,
            overrides.wp_app_password
            or container.credential_cipher.decrypt(site.wp_app_password_encrypted),
            container.build_publisher_from_credentials,
        )
    except WordPressConnectionTestFailedError:
        _record_connection(site, False, overrides, container, clock)
        raise
    _record_connection(site, True, overrides, container, clock)
    return Response(status_code=204)


def _record_connection(
    site: Site, ok: bool, overrides: SiteUpdate, container: Container, clock: Clock
) -> None:
    if overrides.wp_base_url or overrides.wp_username or overrides.wp_app_password:
        return
    container.site_repository.save_site(
        site.model_copy(update={"connection_ok": ok, "connection_checked_at": clock.now()})
    )


@router.get("/sites")
def list_sites_route(container: Container = Depends(get_container)) -> SitesOut:
    summaries = []
    for site in container.site_repository.list_sites():
        # ponytail: one article read per site; store counters on the site
        # when sites × articles gets large.
        articles = container.repository_for(site.id).list_articles()
        summaries.append(
            SiteSummary(
                **_out(site).model_dump(),
                article_count=len(articles),
                needs_attention_count=sum(
                    1 for a in articles if a.status == Status.FAILED or a.sync_warning
                ),
            )
        )
    return SitesOut(sites=summaries)


@router.patch("/sites/{site_id}")
async def update_site_route(
    site_id: str,
    body: SiteUpdate,
    container: Container = Depends(get_container),
    clock: Clock = Depends(get_clock),
) -> SiteOut:
    site = _get_site(site_id, container)
    if not any(body.model_dump().values()):
        raise EmptyUpdateError
    _require_https(body.wp_base_url, container)
    updated = await edit_site(
        site,
        body.name,
        body.wp_base_url,
        body.wp_username,
        body.wp_app_password,
        container.site_repository,
        container.credential_cipher,
        clock,
        container.build_publisher_from_credentials,
    )
    return _out(updated)


@router.delete("/sites/{site_id}", status_code=204)
def delete_site_route(site_id: str, container: Container = Depends(get_container)) -> Response:
    _get_site(site_id, container)
    container.delete_site(site_id)
    return Response(status_code=204)
