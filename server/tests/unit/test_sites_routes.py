from dataclasses import dataclass, field
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.adapters.testing.clock import FixedClock
from app.adapters.testing.in_memory_repository import InMemoryArticleRepository
from app.adapters.testing.in_memory_site_repository import InMemorySiteRepository
from app.adapters.testing.scripted_publisher import ScriptedPublisher
from app.adapters.testing.secret_store import InMemorySecretStore
from app.api.auth import require_session
from app.api.deps import get_clock, get_container
from app.api.main import app
from app.core.domain.errors import WordPressError
from app.core.domain.models import Article
from app.core.domain.statuses import Status, SyncWarning

NOW = datetime(2026, 10, 7, 12, 0, 0, tzinfo=UTC)

SITE_PAYLOAD = {
    "name": "Client A",
    "wp_base_url": "https://client-a.example.com",
    "wp_username": "agency",
    "wp_app_password": "app-password",
}


class FakeCipher:
    def encrypt(self, plaintext: str) -> str:
        return f"enc:{plaintext}"

    def decrypt(self, ciphertext: str) -> str:
        return ciphertext.removeprefix("enc:")


@dataclass
class FakeContainer:
    publisher: ScriptedPublisher
    site_repository: InMemorySiteRepository
    credential_cipher: FakeCipher
    secret_store: InMemorySecretStore
    repos: dict[str, InMemoryArticleRepository] = field(default_factory=dict)
    publisher_calls: list[tuple[str, str, str]] = field(default_factory=list)

    def build_publisher_from_credentials(self, base_url: str, username: str, app_password: str):
        self.publisher_calls.append((base_url, username, app_password))
        return self.publisher

    def repository_for(self, site_id: str) -> InMemoryArticleRepository:
        return self.repos.setdefault(site_id, InMemoryArticleRepository())

    def delete_site(self, site_id: str) -> None:
        self.site_repository.delete_site(site_id)
        self.repos.pop(site_id, None)


@pytest.fixture
def publisher():
    return ScriptedPublisher()


@pytest.fixture
def container(publisher):
    return FakeContainer(
        publisher=publisher,
        site_repository=InMemorySiteRepository(),
        credential_cipher=FakeCipher(),
        secret_store=InMemorySecretStore(),
    )


@pytest.fixture
def client(container):
    app.dependency_overrides[require_session] = lambda: "test-uid"
    app.dependency_overrides[get_container] = lambda: container
    app.dependency_overrides[get_clock] = lambda: FixedClock(NOW)
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_create_site_succeeds(client):
    response = client.post("/sites", json=SITE_PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Client A"
    assert body["wp_base_url"] == "https://client-a.example.com"
    assert body["wp_username"] == "agency"
    assert body["connection_ok"] is True
    assert "wp_app_password" not in body


def test_create_site_returns_wp_connection_failed(client, publisher):
    publisher.check_credentials_error = WordPressError(401, "rest_not_logged_in", "bad password")

    response = client.post("/sites", json=SITE_PAYLOAD)

    assert response.status_code == 422
    assert response.json() == {"code": "wp_connection_failed", "message": "bad password"}


def test_list_sites_returns_created_sites(client):
    created = client.post("/sites", json=SITE_PAYLOAD).json()

    response = client.get("/sites")
    assert response.status_code == 200
    assert {s["id"] for s in response.json()["sites"]} == {created["id"]}


def test_sites_routes_require_session():
    response = TestClient(app).get("/sites")
    assert response.status_code == 401
    assert response.json() == {"code": "invalid_token"}


def _article(id_: str, status: Status, sync_warning: SyncWarning | None = None) -> Article:
    return Article(
        id=id_,
        title="Title",
        slug=id_,
        body_html="<p>hi</p>",
        source="paste",
        status=status,
        sync_warning=sync_warning,
        version=1,
        created_at=NOW,
        updated_at=NOW,
    )


def test_list_sites_counts_articles_per_site(client, container):
    a = client.post("/sites", json=SITE_PAYLOAD).json()["id"]
    b = client.post("/sites", json={**SITE_PAYLOAD, "name": "Client B"}).json()["id"]
    repo = container.repository_for(a)
    repo.create_article(_article("a1", Status.DRAFT))
    repo.create_article(_article("a2", Status.FAILED))
    repo.create_article(_article("a3", Status.PUBLISHED, SyncWarning.LATE))

    sites = {s["id"]: s for s in client.get("/sites").json()["sites"]}

    assert (sites[a]["article_count"], sites[a]["needs_attention_count"]) == (3, 2)
    assert (sites[b]["article_count"], sites[b]["needs_attention_count"]) == (0, 0)


def test_test_connection_succeeds_without_persisting(client, container):
    payload = {k: v for k, v in SITE_PAYLOAD.items() if k != "name"}

    response = client.post("/sites/test-connection", json=payload)

    assert response.status_code == 204
    assert container.site_repository.list_sites() == []


def test_test_connection_returns_wp_connection_failed(client, publisher):
    publisher.check_credentials_error = WordPressError(401, "rest_not_logged_in", "bad password")
    payload = {k: v for k, v in SITE_PAYLOAD.items() if k != "name"}

    response = client.post("/sites/test-connection", json=payload)

    assert response.status_code == 422
    assert response.json()["code"] == "wp_connection_failed"


def test_update_site_name_only_skips_wordpress(client, container):
    site_id = client.post("/sites", json=SITE_PAYLOAD).json()["id"]
    container.publisher_calls.clear()

    response = client.patch(f"/sites/{site_id}", json={"name": "Renamed", "wp_app_password": ""})

    assert response.status_code == 200
    assert response.json()["name"] == "Renamed"
    assert container.publisher_calls == []
    stored = container.site_repository.get_site(site_id)
    assert stored.wp_app_password_encrypted == "enc:app-password"


def test_update_site_url_retests_with_stored_password(client, container):
    site_id = client.post("/sites", json=SITE_PAYLOAD).json()["id"]
    container.publisher_calls.clear()

    response = client.patch(f"/sites/{site_id}", json={"wp_base_url": "https://new.example.com"})

    assert response.status_code == 200
    assert container.publisher_calls == [("https://new.example.com", "agency", "app-password")]


def test_update_site_connection_failure_saves_nothing(client, container, publisher):
    site_id = client.post("/sites", json=SITE_PAYLOAD).json()["id"]
    publisher.check_credentials_error = WordPressError(401, "rest_not_logged_in", "bad password")

    response = client.patch(
        f"/sites/{site_id}", json={"name": "Renamed", "wp_app_password": "wrong"}
    )

    assert response.status_code == 422
    assert response.json()["code"] == "wp_connection_failed"
    stored = container.site_repository.get_site(site_id)
    assert (stored.name, stored.wp_app_password_encrypted) == ("Client A", "enc:app-password")


def test_update_site_with_nothing_returns_empty_update(client):
    site_id = client.post("/sites", json=SITE_PAYLOAD).json()["id"]

    response = client.patch(f"/sites/{site_id}", json={"wp_app_password": ""})

    assert response.status_code == 422
    assert response.json() == {"code": "empty_update"}


def test_delete_site_removes_site_and_articles(client, container):
    site_id = client.post("/sites", json=SITE_PAYLOAD).json()["id"]
    container.repository_for(site_id).create_article(_article("a1", Status.DRAFT))

    response = client.delete(f"/sites/{site_id}")

    assert response.status_code == 204
    assert container.site_repository.get_site(site_id) is None
    assert container.repository_for(site_id).list_articles() == []


@pytest.mark.parametrize("method", ["patch", "delete"])
def test_unknown_site_returns_site_not_found(client, method):
    kwargs = {"json": {"name": "x"}} if method == "patch" else {}
    response = getattr(client, method)("/sites/missing", **kwargs)
    assert response.status_code == 404
    assert response.json() == {"code": "site_not_found"}


def test_stored_site_connection_failure_is_recorded(client, container, publisher):
    site_id = client.post("/sites", json=SITE_PAYLOAD).json()["id"]
    publisher.check_credentials_error = WordPressError(401, "rest_not_logged_in", "revoked")

    response = client.post(f"/sites/{site_id}/test-connection")

    assert response.status_code == 422
    assert container.publisher_calls[-1] == (
        "https://client-a.example.com",
        "agency",
        "app-password",
    )
    assert container.site_repository.get_site(site_id).connection_ok is False


def test_site_connection_with_overrides_is_not_recorded(client, container, publisher):
    site_id = client.post("/sites", json=SITE_PAYLOAD).json()["id"]
    publisher.check_credentials_error = WordPressError(401, "rest_not_logged_in", "bad")

    response = client.post(
        f"/sites/{site_id}/test-connection", json={"wp_base_url": "https://new.example.com"}
    )

    assert response.status_code == 422
    assert container.publisher_calls[-1][0] == "https://new.example.com"
    assert container.site_repository.get_site(site_id).connection_ok is True
