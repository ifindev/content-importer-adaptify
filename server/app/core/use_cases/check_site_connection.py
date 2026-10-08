from collections.abc import Callable

from app.core.domain.errors import WordPressConnectionTestFailedError, WordPressError
from app.core.ports.publisher import Publisher


async def check_site_connection(
    wp_base_url: str,
    wp_username: str,
    wp_app_password: str,
    build_publisher: Callable[[str, str, str], Publisher],
) -> None:
    """Raises WordPressConnectionTestFailedError when WordPress rejects the credentials."""
    publisher = build_publisher(wp_base_url, wp_username, wp_app_password)
    try:
        await publisher.check_credentials()
    except WordPressError as exc:
        raise WordPressConnectionTestFailedError(exc.message or str(exc)) from exc
