from datetime import UTC, datetime

import pytest

from app.adapters.testing.clock import FixedClock
from app.adapters.testing.in_memory_repository import InMemoryArticleRepository
from app.adapters.testing.secret_store import InMemorySecretStore
from app.core.domain.models import Site
from app.core.lib.tokens import hash_token
from app.core.use_cases.review_link import get_or_create_review_link, reset_review_link

NOW = datetime(2026, 10, 7, 12, 0, 0, tzinfo=UTC)
WEB_BASE_URL = "https://app.example.com"
SITE_ID = "s1"


@pytest.fixture
def repository():
    repo = InMemoryArticleRepository()
    repo.save_site(Site(id=SITE_ID, name="Test site", wp_base_url="https://wp.example.com"))
    return repo


@pytest.fixture
def secret_store():
    return InMemorySecretStore()


@pytest.fixture
def clock():
    return FixedClock(NOW)


def test_fresh_install_generates_and_persists_token(repository, secret_store, clock):
    url, created_at = get_or_create_review_link(
        SITE_ID, repository, secret_store, clock, WEB_BASE_URL
    )

    assert url.startswith(f"{WEB_BASE_URL}/review/")
    assert created_at == NOW
    assert secret_store.get_review_token(SITE_ID) is not None
    assert repository.get_site().review_token_hash == hash_token(
        secret_store.get_review_token(SITE_ID)
    )


def test_second_call_returns_the_same_token(repository, secret_store, clock):
    first_url, first_created_at = get_or_create_review_link(
        SITE_ID, repository, secret_store, clock, WEB_BASE_URL
    )
    second_url, second_created_at = get_or_create_review_link(
        SITE_ID, repository, secret_store, clock, WEB_BASE_URL
    )

    assert first_url == second_url
    assert first_created_at == second_created_at


def test_reset_invalidates_old_hash_and_returns_a_new_token(repository, secret_store, clock):
    get_or_create_review_link(SITE_ID, repository, secret_store, clock, WEB_BASE_URL)
    old_hash = repository.get_site().review_token_hash

    new_url, _ = reset_review_link(SITE_ID, repository, secret_store, clock, WEB_BASE_URL)

    assert repository.get_site().review_token_hash != old_hash
    assert new_url.startswith(f"{WEB_BASE_URL}/review/")
    assert (
        hash_token(secret_store.get_review_token(SITE_ID))
        == repository.get_site().review_token_hash
    )
