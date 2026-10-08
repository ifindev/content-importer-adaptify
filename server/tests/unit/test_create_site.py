from datetime import UTC, datetime

import pytest

from app.adapters.testing.clock import FixedClock
from app.adapters.testing.in_memory_site_repository import InMemorySiteRepository
from app.adapters.testing.scripted_publisher import ScriptedPublisher
from app.adapters.testing.secret_store import InMemorySecretStore
from app.core.domain.errors import WordPressConnectionTestFailedError, WordPressError
from app.core.lib.tokens import hash_token
from app.core.use_cases.create_site import create_site

pytestmark = pytest.mark.anyio

NOW = datetime(2026, 10, 7, 12, 0, 0, tzinfo=UTC)


class FakeCipher:
    """# ponytail: reversible string tagging, not real crypto — proves the use case
    calls encrypt/decrypt through the port without needing a real Fernet key in tests."""

    def encrypt(self, plaintext: str) -> str:
        return f"enc:{plaintext}"

    def decrypt(self, ciphertext: str) -> str:
        return ciphertext.removeprefix("enc:")


async def test_create_site_succeeds_and_mints_a_review_token():
    site_repository = InMemorySiteRepository()
    secret_store = InMemorySecretStore()
    publisher = ScriptedPublisher()

    site = await create_site(
        "Client A",
        "https://client-a.example.com",
        "agency",
        "secret-app-password",
        site_repository,
        FakeCipher(),
        secret_store,
        FixedClock(NOW),
        build_publisher=lambda *_: publisher,
    )

    assert site_repository.get_site(site.id) == site
    assert site.wp_app_password_encrypted == "enc:secret-app-password"
    token = secret_store.get_review_token(site.id)
    assert token is not None
    assert site.review_token_hash == hash_token(token)
    assert site.review_token_created_at == NOW
    assert (site.connection_ok, site.connection_checked_at) == (True, NOW)


async def test_create_site_raises_on_wordpress_connection_failure():
    publisher = ScriptedPublisher()
    publisher.check_credentials_error = WordPressError(401, "rest_not_logged_in", "bad password")

    with pytest.raises(WordPressConnectionTestFailedError):
        await create_site(
            "Client A",
            "https://client-a.example.com",
            "agency",
            "wrong-password",
            InMemorySiteRepository(),
            FakeCipher(),
            InMemorySecretStore(),
            FixedClock(NOW),
            build_publisher=lambda *_: publisher,
        )
