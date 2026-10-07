from dataclasses import dataclass
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.adapters.testing.clock import FixedClock
from app.adapters.testing.in_memory_site_repository import InMemorySiteRepository
from app.adapters.testing.scripted_publisher import ScriptedPublisher
from app.adapters.testing.secret_store import InMemorySecretStore
from app.api.auth import require_session
from app.api.deps import get_clock, get_container
from app.api.main import app
from app.core.domain.errors import WordPressError

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

    def build_publisher_from_credentials(self, base_url: str, username: str, app_password: str):
        return self.publisher


@pytest.fixture
def publisher():
    return ScriptedPublisher()


@pytest.fixture
def client(publisher):
    container = FakeContainer(
        publisher=publisher,
        site_repository=InMemorySiteRepository(),
        credential_cipher=FakeCipher(),
        secret_store=InMemorySecretStore(),
    )
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
    assert "wp_app_password" not in body
    assert "wp_username" not in body


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
