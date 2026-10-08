from datetime import UTC, datetime

import pytest
from cryptography.fernet import Fernet

from app.adapters.crypto.fernet_cipher import FernetCredentialCipher
from app.adapters.testing.clock import FixedClock
from app.adapters.testing.in_memory_repository import InMemoryArticleRepository
from app.core.domain.models import Site
from app.core.lib.tokens import hash_token
from app.core.use_cases.review_link import get_or_create_review_link, reset_review_link

NOW = datetime(2026, 10, 7, 12, 0, 0, tzinfo=UTC)
WEB_BASE_URL = "https://app.example.com"
SITE_ID = "s1"


def _token(url: str) -> str:
    return url.removeprefix(f"{WEB_BASE_URL}/review/")


@pytest.fixture
def repository():
    repo = InMemoryArticleRepository()
    repo.save_site(Site(id=SITE_ID, name="Test site", wp_base_url="https://wp.example.com"))
    return repo


@pytest.fixture
def cipher():
    return FernetCredentialCipher(Fernet.generate_key().decode())


@pytest.fixture
def clock():
    return FixedClock(NOW)


def test_site_without_a_stored_token_gets_one(repository, cipher, clock):
    url, created_at = get_or_create_review_link(repository, cipher, clock, WEB_BASE_URL)

    site = repository.get_site()
    assert url.startswith(f"{WEB_BASE_URL}/review/")
    assert created_at == NOW
    assert cipher.decrypt(site.review_token_encrypted) == _token(url)
    assert site.review_token_hash == hash_token(_token(url))


def test_second_call_returns_the_same_token(repository, cipher, clock):
    first = get_or_create_review_link(repository, cipher, clock, WEB_BASE_URL)
    second = get_or_create_review_link(repository, cipher, clock, WEB_BASE_URL)

    assert first == second


def test_reset_invalidates_old_hash_and_returns_a_new_token(repository, cipher, clock):
    old_url, _ = get_or_create_review_link(repository, cipher, clock, WEB_BASE_URL)

    new_url, _ = reset_review_link(repository, cipher, clock, WEB_BASE_URL)

    site = repository.get_site()
    assert new_url != old_url
    assert site.review_token_hash == hash_token(_token(new_url))
    assert site.review_token_hash != hash_token(_token(old_url))
    assert get_or_create_review_link(repository, cipher, clock, WEB_BASE_URL)[0] == new_url


def test_token_under_another_key_rotates_once_then_stays(repository, cipher, clock):
    other = FernetCredentialCipher(Fernet.generate_key().decode())
    old_url, _ = get_or_create_review_link(repository, other, clock, WEB_BASE_URL)

    first, _ = get_or_create_review_link(repository, cipher, clock, WEB_BASE_URL)
    second, _ = get_or_create_review_link(repository, cipher, clock, WEB_BASE_URL)

    assert first != old_url
    assert first == second
