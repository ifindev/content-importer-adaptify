from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.adapters.testing.clock import FixedClock
from app.adapters.testing.in_memory_repository import InMemoryArticleRepository
from app.adapters.testing.scripted_publisher import ScriptedPublisher
from app.api.auth import require_session
from app.api.deps import (
    SiteContext,
    get_clock,
    get_document_parser,
    get_site_context,
    get_sync_cache,
)
from app.api.main import app
from app.core.domain.models import Article, Site
from app.core.domain.statuses import Status
from app.core.ports.document_parser import ParsedDocument
from app.core.use_cases.sync_status import SyncCache

NOW = datetime(2026, 10, 7, 12, 0, 0, tzinfo=UTC)
SITE_ID = "s1"


class FakeParser:
    def clean_html(self, html: str) -> ParsedDocument:
        return ParsedDocument(title=None, body_html=html)


def _article(id_: str, status: Status = Status.DRAFT) -> Article:
    return Article(
        id=id_,
        title="Title",
        slug="title",
        body_html="<p>hi</p>",
        source="paste",
        status=status,
        version=1,
        created_at=NOW,
        updated_at=NOW,
    )


@pytest.fixture
def repository():
    return InMemoryArticleRepository()


@pytest.fixture
def client(repository):
    site_context = SiteContext(
        site_id=SITE_ID,
        site=Site(id=SITE_ID, name="Test site", wp_base_url="http://wp.test"),
        repository=repository,
        publisher=ScriptedPublisher(),
    )
    app.dependency_overrides[require_session] = lambda: "test-uid"
    app.dependency_overrides[get_site_context] = lambda: site_context
    app.dependency_overrides[get_document_parser] = lambda: FakeParser()
    app.dependency_overrides[get_clock] = lambda: FixedClock(NOW)
    app.dependency_overrides[get_sync_cache] = lambda: SyncCache()
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_list_articles(client, repository):
    repository.create_article(_article("a1", Status.DRAFT))
    repository.create_article(_article("a2", Status.APPROVED))

    response = client.get(f"/sites/{SITE_ID}/articles")
    assert response.status_code == 200
    assert {a["id"] for a in response.json()["articles"]} == {"a1", "a2"}


def test_list_articles_filters_by_status(client, repository):
    repository.create_article(_article("a1", Status.DRAFT))
    repository.create_article(_article("a2", Status.APPROVED))

    response = client.get(f"/sites/{SITE_ID}/articles", params={"status": "approved"})
    assert response.status_code == 200
    assert [a["id"] for a in response.json()["articles"]] == ["a2"]


def test_list_articles_rejects_bad_status(client):
    response = client.get(f"/sites/{SITE_ID}/articles", params={"status": "bogus"})
    assert response.status_code == 422


def test_get_article(client, repository):
    repository.create_article(_article("a1"))
    response = client.get(f"/sites/{SITE_ID}/articles/a1")
    assert response.status_code == 200
    assert response.json()["id"] == "a1"
    assert response.json()["events"] == []


def test_get_article_not_found(client):
    response = client.get(f"/sites/{SITE_ID}/articles/missing")
    assert response.status_code == 404
    assert response.json() == {"code": "not_found"}


def test_articles_require_session():
    response = TestClient(app).get(f"/sites/{SITE_ID}/articles")
    assert response.status_code == 401
    assert response.json() == {"code": "invalid_token"}


@pytest.mark.parametrize("status", [Status.DRAFT, Status.CHANGES_REQUESTED])
def test_patch_article_from_editable_status(client, repository, status):
    repository.create_article(_article("a1", status))
    response = client.patch(f"/sites/{SITE_ID}/articles/a1", json={"title": "New Title"})
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "New Title"
    assert body["status"] == status.value
    assert body["version"] == 2


@pytest.mark.parametrize("status", [Status.APPROVED, Status.SCHEDULED])
def test_patch_article_from_approved_or_scheduled_resets_to_draft(client, repository, status):
    repository.create_article(_article("a1", status))
    response = client.patch(f"/sites/{SITE_ID}/articles/a1", json={"title": "New Title"})
    assert response.status_code == 200
    assert response.json()["status"] == "draft"


@pytest.mark.parametrize("status", [Status.AWAITING_APPROVAL, Status.PUBLISHED, Status.FAILED])
def test_patch_article_from_non_editable_status_returns_409(client, repository, status):
    repository.create_article(_article("a1", status))
    response = client.patch(f"/sites/{SITE_ID}/articles/a1", json={"title": "New Title"})
    assert response.status_code == 409
    assert response.json() == {"code": "not_editable"}


def test_patch_article_not_found_returns_404(client):
    response = client.patch(f"/sites/{SITE_ID}/articles/missing", json={"title": "x"})
    assert response.status_code == 404
    assert response.json() == {"code": "not_found"}


def test_patch_article_empty_body_returns_422(client, repository):
    repository.create_article(_article("a1"))
    response = client.patch(f"/sites/{SITE_ID}/articles/a1", json={})
    assert response.status_code == 422
    assert response.json() == {"code": "empty_update"}


def test_patch_article_oversized_body_html_returns_413(client, repository):
    repository.create_article(_article("a1"))
    huge = "a" * (2 * 1024 * 1024 + 1)
    response = client.patch(f"/sites/{SITE_ID}/articles/a1", json={"body_html": huge})
    assert response.status_code == 413
    assert response.json() == {"code": "payload_too_large"}


def test_patch_article_malformed_slug_returns_422(client, repository):
    repository.create_article(_article("a1"))
    response = client.patch(f"/sites/{SITE_ID}/articles/a1", json={"slug": "Not A Slug!"})
    assert response.status_code == 422


@pytest.mark.parametrize("status", [Status.DRAFT, Status.CHANGES_REQUESTED])
def test_send_for_review_from_sendable_status(client, repository, status):
    repository.create_article(_article("a1", status))
    response = client.post(f"/sites/{SITE_ID}/articles/a1/send-for-review")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "awaiting_approval"
    assert body["events"][-1]["type"] == "sent_for_review"


@pytest.mark.parametrize(
    "status", [Status.AWAITING_APPROVAL, Status.APPROVED, Status.PUBLISHED, Status.FAILED]
)
def test_send_for_review_from_other_status_returns_409(client, repository, status):
    repository.create_article(_article("a1", status))
    response = client.post(f"/sites/{SITE_ID}/articles/a1/send-for-review")
    assert response.status_code == 409
    assert response.json() == {"code": "not_sendable"}


def test_send_for_review_not_found_returns_404(client):
    response = client.post(f"/sites/{SITE_ID}/articles/missing/send-for-review")
    assert response.status_code == 404
    assert response.json() == {"code": "not_found"}


def test_pull_back_from_awaiting_approval(client, repository):
    repository.create_article(_article("a1", Status.AWAITING_APPROVAL))
    response = client.post(f"/sites/{SITE_ID}/articles/a1/pull-back")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "draft"
    assert body["events"][-1]["type"] == "pulled_back"


@pytest.mark.parametrize("status", [Status.DRAFT, Status.APPROVED, Status.PUBLISHED])
def test_pull_back_from_other_status_returns_409(client, repository, status):
    repository.create_article(_article("a1", status))
    response = client.post(f"/sites/{SITE_ID}/articles/a1/pull-back")
    assert response.status_code == 409
    assert response.json() == {"code": "not_awaiting_approval"}


def test_pull_back_not_found_returns_404(client):
    response = client.post(f"/sites/{SITE_ID}/articles/missing/pull-back")
    assert response.status_code == 404
    assert response.json() == {"code": "not_found"}


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (Status.DRAFT, 204),
        (Status.CHANGES_REQUESTED, 204),
        (Status.AWAITING_APPROVAL, 409),
        (Status.APPROVED, 409),
        (Status.SCHEDULED, 409),
        (Status.PUBLISHED, 409),
        (Status.FAILED, 409),
    ],
)
def test_delete_article_by_status(client, repository, status, expected):
    repository.create_article(_article("a1", status))

    response = client.delete(f"/sites/{SITE_ID}/articles/a1")

    assert response.status_code == expected
    if expected == 204:
        assert repository.get_article("a1") is None
        assert repository.list_events("a1") == []
    else:
        assert response.json() == {"code": "not_deletable"}
        assert repository.get_article("a1") is not None


def test_delete_unknown_article_returns_404(client):
    response = client.delete(f"/sites/{SITE_ID}/articles/missing")
    assert response.status_code == 404
    assert response.json() == {"code": "not_found"}
