import uuid
from collections.abc import Callable

from app.core.domain.errors import WordPressConnectionTestFailedError, WordPressError
from app.core.domain.models import Site
from app.core.lib.tokens import generate_token, hash_token
from app.core.ports.clock import Clock
from app.core.ports.credential_cipher import CredentialCipher
from app.core.ports.publisher import Publisher
from app.core.ports.secret_store import SecretStore
from app.core.ports.site_repository import SiteRepository


async def create_site(
    name: str,
    wp_base_url: str,
    wp_username: str,
    wp_app_password: str,
    site_repository: SiteRepository,
    credential_cipher: CredentialCipher,
    secret_store: SecretStore,
    clock: Clock,
    build_publisher: Callable[[str, str, str], Publisher],
) -> Site:
    publisher = build_publisher(wp_base_url, wp_username, wp_app_password)
    try:
        await publisher.check_credentials()
    except WordPressError as exc:
        raise WordPressConnectionTestFailedError(exc.message or str(exc)) from exc

    token = generate_token()
    site = Site(
        id=str(uuid.uuid4()),
        name=name,
        wp_base_url=wp_base_url,
        wp_username=wp_username,
        wp_app_password_encrypted=credential_cipher.encrypt(wp_app_password),
        review_token_hash=hash_token(token),
        review_token_created_at=clock.now(),
    )
    site_repository.create_site(site)
    secret_store.set_review_token(site.id, token)
    return site
