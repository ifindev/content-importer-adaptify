import uuid

import httpx
import pytest
from fastapi import Depends
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.anyio, pytest.mark.integration]

AUTH_EMULATOR_HOST = "localhost:9099"
PROJECT_ID = "demo-content-importer"


def _mint_id_token() -> str:
    url = (
        f"http://{AUTH_EMULATOR_HOST}/identitytoolkit.googleapis.com/v1/"
        "accounts:signUp?key=fake-api-key"
    )
    response = httpx.post(
        url,
        json={
            "email": f"t-012-{uuid.uuid4()}@example.com",
            "password": "password123",
            "returnSecureToken": True,
        },
    )
    response.raise_for_status()
    return response.json()["idToken"]


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("FIREBASE_AUTH_EMULATOR_HOST", AUTH_EMULATOR_HOST)
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", PROJECT_ID)

    import importlib

    import app.api.auth as auth_module
    import app.api.main as main_module
    import app.api.routes.auth as routes_auth_module

    importlib.reload(auth_module)
    importlib.reload(routes_auth_module)
    importlib.reload(main_module)

    from app.api.auth import require_session

    @main_module.app.get("/_protected")
    def _protected(uid: str = Depends(require_session)) -> dict[str, str]:
        return {"uid": uid}

    with TestClient(main_module.app, base_url="https://testserver") as test_client:
        yield test_client


async def test_session_endpoint_sets_cookie_and_protects_route(client):
    id_token = _mint_id_token()

    response = client.post("/auth/session", json={"id_token": id_token})
    assert response.status_code == 204
    assert "session" in response.cookies

    protected = client.get("/_protected")
    assert protected.status_code == 200
    assert "uid" in protected.json()


async def test_protected_route_rejects_missing_cookie(client):
    response = client.get("/_protected", cookies={})
    assert response.status_code == 401
    assert response.json() == {"code": "invalid_token"}


async def test_session_endpoint_rejects_invalid_id_token(client):
    response = client.post("/auth/session", json={"id_token": "not-a-real-token"})
    assert response.status_code == 401
    assert response.json() == {"code": "invalid_token"}
