from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.adapters.testing.in_memory_repository import InMemoryArticleRepository
from app.api.auth import require_session
from app.api.main import app
from app.api.routes.articles import get_repository
from app.core.domain.models import Article
from app.core.domain.statuses import Status

NOW = datetime(2026, 10, 7, 12, 0, 0, tzinfo=UTC)


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
    app.dependency_overrides[require_session] = lambda: "test-uid"
    app.dependency_overrides[get_repository] = lambda: repository
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_list_articles(client, repository):
    repository.create_article(_article("a1", Status.DRAFT))
    repository.create_article(_article("a2", Status.APPROVED))

    response = client.get("/articles")
    assert response.status_code == 200
    assert {a["id"] for a in response.json()["articles"]} == {"a1", "a2"}


def test_list_articles_filters_by_status(client, repository):
    repository.create_article(_article("a1", Status.DRAFT))
    repository.create_article(_article("a2", Status.APPROVED))

    response = client.get("/articles", params={"status": "approved"})
    assert response.status_code == 200
    assert [a["id"] for a in response.json()["articles"]] == ["a2"]


def test_list_articles_rejects_bad_status(client):
    response = client.get("/articles", params={"status": "bogus"})
    assert response.status_code == 422


def test_get_article(client, repository):
    repository.create_article(_article("a1"))
    response = client.get("/articles/a1")
    assert response.status_code == 200
    assert response.json()["id"] == "a1"
    assert response.json()["events"] == []


def test_get_article_not_found(client):
    response = client.get("/articles/missing")
    assert response.status_code == 404
    assert response.json() == {"code": "not_found"}


def test_articles_require_session():
    app.dependency_overrides[get_repository] = lambda: InMemoryArticleRepository()
    response = TestClient(app).get("/articles")
    app.dependency_overrides.clear()
    assert response.status_code == 401
    assert response.json() == {"code": "invalid_token"}
