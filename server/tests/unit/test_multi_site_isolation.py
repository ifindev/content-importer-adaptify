from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.adapters.testing.clock import FixedClock
from app.adapters.testing.in_memory_repository import InMemoryArticleRepository
from app.adapters.testing.scripted_publisher import ScriptedPublisher
from app.api.auth import require_session
from app.api.deps import SiteContext, get_clock, get_site_context, get_sync_cache
from app.api.main import app
from app.core.domain.models import Article, Site
from app.core.domain.statuses import Status
from app.core.use_cases.sync_status import SyncCache

NOW = datetime(2026, 10, 7, 12, 0, 0, tzinfo=UTC)


def _article(id_: str) -> Article:
    return Article(
        id=id_,
        title="Title",
        slug=id_,
        body_html="<p>hi</p>",
        source="paste",
        status=Status.DRAFT,
        version=1,
        created_at=NOW,
        updated_at=NOW,
    )


def _site_context(site_id: str, repository: InMemoryArticleRepository) -> SiteContext:
    return SiteContext(
        site_id=site_id,
        site=Site(id=site_id, name=f"Site {site_id}", wp_base_url="http://wp.test"),
        repository=repository,
        publisher=ScriptedPublisher(),
    )


@pytest.fixture
def client():
    app.dependency_overrides[require_session] = lambda: "test-uid"
    app.dependency_overrides[get_clock] = lambda: FixedClock(NOW)
    app.dependency_overrides[get_sync_cache] = lambda: SyncCache()
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_an_article_in_one_site_never_shows_in_another_sites_list(client):
    repo_a = InMemoryArticleRepository()
    repo_a.create_article(_article("only-in-a"))
    repo_b = InMemoryArticleRepository()
    repo_b.create_article(_article("only-in-b"))

    app.dependency_overrides[get_site_context] = lambda: _site_context("site-a", repo_a)
    response_a = client.get("/sites/site-a/articles")

    app.dependency_overrides[get_site_context] = lambda: _site_context("site-b", repo_b)
    response_b = client.get("/sites/site-b/articles")

    assert [a["id"] for a in response_a.json()["articles"]] == ["only-in-a"]
    assert [a["id"] for a in response_b.json()["articles"]] == ["only-in-b"]
