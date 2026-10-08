import uuid
from collections.abc import Callable

from app.core.domain.models import Site
from app.core.lib.tokens import generate_token, hash_token
from app.core.ports.clock import Clock
from app.core.ports.credential_cipher import CredentialCipher
from app.core.ports.publisher import Publisher
from app.core.ports.site_repository import SiteRepository
from app.core.use_cases.check_site_connection import check_site_connection


async def create_site(
    name: str,
    wp_base_url: str,
    wp_username: str,
    wp_app_password: str,
    site_repository: SiteRepository,
    credential_cipher: CredentialCipher,
    clock: Clock,
    build_publisher: Callable[[str, str, str], Publisher],
) -> Site:
    await check_site_connection(wp_base_url, wp_username, wp_app_password, build_publisher)

    token = generate_token()
    now = clock.now()
    site = Site(
        id=str(uuid.uuid4()),
        name=name,
        wp_base_url=wp_base_url,
        wp_username=wp_username,
        wp_app_password_encrypted=credential_cipher.encrypt(wp_app_password),
        review_token_hash=hash_token(token),
        review_token_encrypted=credential_cipher.encrypt(token),
        review_token_created_at=now,
        connection_ok=True,
        connection_checked_at=now,
    )
    site_repository.create_site(site)
    return site
