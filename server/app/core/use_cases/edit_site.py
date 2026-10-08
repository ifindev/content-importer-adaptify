from collections.abc import Callable

from app.core.domain.models import Site
from app.core.ports.clock import Clock
from app.core.ports.credential_cipher import CredentialCipher
from app.core.ports.publisher import Publisher
from app.core.ports.site_repository import SiteRepository
from app.core.use_cases.check_site_connection import check_site_connection


async def edit_site(
    site: Site,
    name: str | None,
    wp_base_url: str | None,
    wp_username: str | None,
    wp_app_password: str | None,
    site_repository: SiteRepository,
    credential_cipher: CredentialCipher,
    clock: Clock,
    build_publisher: Callable[[str, str, str], Publisher],
) -> Site:
    """Saves the given fields. A changed URL, username or password is tested
    against WordPress first; a failure raises and nothing is saved. An empty
    password keeps the stored one."""
    updates: dict = {}
    if name:
        updates["name"] = name
    if wp_base_url and wp_base_url != site.wp_base_url:
        updates["wp_base_url"] = wp_base_url
    if wp_username and wp_username != site.wp_username:
        updates["wp_username"] = wp_username

    if "wp_base_url" in updates or "wp_username" in updates or wp_app_password:
        password = wp_app_password or credential_cipher.decrypt(site.wp_app_password_encrypted)
        await check_site_connection(
            updates.get("wp_base_url", site.wp_base_url),
            updates.get("wp_username", site.wp_username),
            password,
            build_publisher,
        )
        updates["wp_app_password_encrypted"] = credential_cipher.encrypt(password)
        updates["connection_ok"] = True
        updates["connection_checked_at"] = clock.now()

    updated = site.model_copy(update=updates)
    site_repository.save_site(updated)
    return updated
