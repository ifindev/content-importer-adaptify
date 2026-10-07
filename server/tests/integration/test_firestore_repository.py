import uuid
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from google.cloud import firestore

from app.adapters.firestore.repository import FirestoreArticleRepository
from app.adapters.testing.clock import FixedClock
from app.adapters.testing.secret_store import InMemorySecretStore
from app.api.auth import require_session
from app.api.main import app
from app.api.routes.articles import get_clock as get_articles_clock
from app.api.routes.articles import get_repository
from app.api.routes.review_link import get_clock, get_secret_store, get_web_base_url
from app.api.routes.review_link import get_repository as get_review_link_repository
from app.core.domain.models import Article, Event
from app.core.domain.statuses import EventType, Status

pytestmark = pytest.mark.integration

FIRESTORE_EMULATOR_HOST = "localhost:8081"
PROJECT_ID = "demo-content-importer"


@pytest.fixture
def repository(monkeypatch):
    monkeypatch.setenv("FIRESTORE_EMULATOR_HOST", FIRESTORE_EMULATOR_HOST)
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", PROJECT_ID)
    client = firestore.Client()
    return FirestoreArticleRepository(client, site_id=f"test-{uuid.uuid4()}")


def _article(id_: str, status: Status = Status.DRAFT) -> Article:
    now = datetime.now(UTC)
    return Article(
        id=id_,
        title="Title",
        slug="title",
        body_html="<p>hi</p>",
        source="paste",
        status=status,
        version=1,
        created_at=now,
        updated_at=now,
    )


def test_ensure_site_bootstrapped_is_idempotent(repository):
    first = repository.ensure_site_bootstrapped("My Site", "https://wp.example")
    second = repository.ensure_site_bootstrapped("Other name", "https://other.example")

    assert first == second
    assert repository.get_site().name == "My Site"


def test_create_and_get_article_round_trip(repository):
    article = repository.create_article(_article("a1"))
    assert repository.get_article("a1") == article


def test_get_article_missing_returns_none(repository):
    assert repository.get_article("missing") is None


def test_save_article_appends_event(repository):
    article = repository.create_article(_article("a1"))
    updated = article.model_copy(update={"status": Status.AWAITING_APPROVAL})
    event = Event(id="e1", type=EventType.SENT_FOR_REVIEW, actor="agency", at=article.updated_at)

    repository.save_article(updated, event)

    assert repository.get_article("a1").status == Status.AWAITING_APPROVAL
    assert [e.id for e in repository.list_events("a1")] == ["e1"]


def test_list_articles_filters_by_status(repository):
    repository.create_article(_article("a1", Status.DRAFT))
    repository.create_article(_article("a2", Status.APPROVED))

    assert {a.id for a in repository.list_articles()} == {"a1", "a2"}
    assert [a.id for a in repository.list_articles(status=Status.APPROVED)] == ["a2"]


def test_articles_routes_work_against_the_firestore_emulator(repository):
    repository.create_article(_article("a1"))
    app.dependency_overrides[require_session] = lambda: "test-uid"
    app.dependency_overrides[get_repository] = lambda: repository
    try:
        client = TestClient(app)
        list_response = client.get("/articles")
        detail_response = client.get("/articles/a1")
    finally:
        app.dependency_overrides.clear()

    assert list_response.status_code == 200
    assert [a["id"] for a in list_response.json()["articles"]] == ["a1"]
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == "a1"


def test_send_for_review_route_works_against_the_firestore_emulator(repository):
    repository.create_article(_article("a1", Status.DRAFT))
    app.dependency_overrides[require_session] = lambda: "test-uid"
    app.dependency_overrides[get_repository] = lambda: repository
    app.dependency_overrides[get_articles_clock] = lambda: FixedClock(datetime.now(UTC))
    try:
        client = TestClient(app)
        response = client.post("/articles/a1/send-for-review")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "awaiting_approval"
    events = repository.list_events("a1")
    assert events[-1].type == EventType.SENT_FOR_REVIEW
    assert events[-1].actor == "test-uid"


def test_review_link_routes_work_against_the_firestore_emulator(repository):
    repository.ensure_site_bootstrapped("Test Site", "https://wp.example.com")
    secret_store = InMemorySecretStore()
    app.dependency_overrides[require_session] = lambda: "test-uid"
    app.dependency_overrides[get_review_link_repository] = lambda: repository
    app.dependency_overrides[get_secret_store] = lambda: secret_store
    app.dependency_overrides[get_clock] = lambda: FixedClock(datetime.now(UTC))
    app.dependency_overrides[get_web_base_url] = lambda: "https://app.example.com"
    try:
        client = TestClient(app)
        first = client.get("/review-link")
        second = client.get("/review-link")
        reset = client.post("/review-link/reset")
    finally:
        app.dependency_overrides.clear()

    assert first.status_code == 200
    assert first.json()["url"] == second.json()["url"]
    assert reset.status_code == 200
    assert reset.json()["url"] != first.json()["url"]
    assert repository.get_site().review_token_hash is not None
