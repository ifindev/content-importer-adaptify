from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.adapters.testing.clock import FixedClock
from app.adapters.testing.in_memory_repository import InMemoryArticleRepository
from app.adapters.testing.scripted_publisher import ScriptedPublisher
from app.api.auth import require_session
from app.api.deps import SiteContext, get_clock, get_site_context, get_sync_cache
from app.api.main import app
from app.core.domain.errors import WordPressError
from app.core.domain.models import Article, Site
from app.core.domain.statuses import Status
from app.core.use_cases.sync_status import SyncCache

NOW = datetime(2026, 10, 7, 12, 0, 0, tzinfo=UTC)
SITE_ID = "s1"


def _article(id_: str, status: Status = Status.DRAFT, **overrides) -> Article:
    return Article(
        id=id_,
        title="Title",
        slug=id_,
        body_html="<p>hi</p>",
        source="paste",
        status=status,
        version=1,
        created_at=NOW,
        updated_at=NOW,
        **overrides,
    )


@pytest.fixture
def repository():
    return InMemoryArticleRepository()


@pytest.fixture
def publisher():
    return ScriptedPublisher()


@pytest.fixture
def client(repository, publisher):
    site_context = SiteContext(
        site_id=SITE_ID,
        site=Site(id=SITE_ID, name="Test site", wp_base_url="http://wp.test"),
        repository=repository,
        publisher=publisher,
    )
    app.dependency_overrides[require_session] = lambda: "test-uid"
    app.dependency_overrides[get_site_context] = lambda: site_context
    app.dependency_overrides[get_clock] = lambda: FixedClock(NOW)
    app.dependency_overrides[get_sync_cache] = lambda: SyncCache()
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_report_empty(client):
    response = client.get(f"/sites/{SITE_ID}/report")
    assert response.status_code == 200
    body = response.json()
    assert body["status_counts"] == {s.value: 0 for s in Status}
    assert body["published_this_month"] == 0
    assert body["avg_approval_seconds"] is None
    assert body["change_rounds"] == []
    assert body["upcoming"] == []
    assert body["published"] == []
    assert body["needs_attention"] == []
    assert body["wordpress_unreachable"] is False


def test_report_lists_failed_article_in_needs_attention(client, repository):
    repository.create_article(_article("a1", Status.FAILED, last_error="boom"))
    response = client.get(f"/sites/{SITE_ID}/report")
    assert response.status_code == 200
    needs_attention = response.json()["needs_attention"]
    assert needs_attention == [
        {"article_id": "a1", "title": "Title", "reason": "failed", "detail": "boom"}
    ]


def test_report_reflects_wordpress_unreachable(client, repository, publisher):
    repository.create_article(_article("a1", Status.SCHEDULED, wp_post_id=1))
    publisher.get_statuses_error = WordPressError(502, code="unreachable", message="down")
    response = client.get(f"/sites/{SITE_ID}/report")
    assert response.status_code == 200
    assert response.json()["wordpress_unreachable"] is True


def test_report_requires_session():
    response = TestClient(app).get(f"/sites/{SITE_ID}/report")
    assert response.status_code == 401
