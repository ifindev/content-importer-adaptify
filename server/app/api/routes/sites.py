from fastapi import APIRouter, Depends

from app.api.auth import require_session
from app.api.deps import get_clock, get_container
from app.api.schemas.sites import SiteCreate, SiteOut, SitesOut
from app.api.tags import SITES
from app.container import Container
from app.core.ports.clock import Clock
from app.core.use_cases.create_site import create_site

router = APIRouter(tags=[SITES], dependencies=[Depends(require_session)])


@router.post("/sites", status_code=201)
async def create_site_route(
    body: SiteCreate,
    container: Container = Depends(get_container),
    clock: Clock = Depends(get_clock),
) -> SiteOut:
    site = await create_site(
        body.name,
        body.wp_base_url,
        body.wp_username,
        body.wp_app_password,
        container.site_repository,
        container.credential_cipher,
        container.secret_store,
        clock,
        container.build_publisher_from_credentials,
    )
    return SiteOut(**site.model_dump(include={"id", "name", "wp_base_url"}))


@router.get("/sites")
def list_sites_route(container: Container = Depends(get_container)) -> SitesOut:
    sites = container.site_repository.list_sites()
    return SitesOut(
        sites=[SiteOut(**s.model_dump(include={"id", "name", "wp_base_url"})) for s in sites]
    )
