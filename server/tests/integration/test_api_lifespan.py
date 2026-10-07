import logging

import pytest
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


async def test_lifespan_logs_ok_with_good_credentials(caplog):
    from app.api.main import app

    with caplog.at_level(logging.INFO, logger="app.api.main"):
        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200

    assert "WordPress credentials OK" in caplog.text


async def test_lifespan_logs_error_with_bad_credentials_and_keeps_running(caplog, monkeypatch):
    monkeypatch.setenv("WP_APP_PASSWORD", "definitely-wrong")

    import importlib

    import app.api.main as main_module

    importlib.reload(main_module)

    with caplog.at_level(logging.ERROR, logger="app.api.main"):
        with TestClient(main_module.app) as client:
            response = client.get("/health")
            assert response.status_code == 200

    assert "WordPress credential check failed" in caplog.text

    monkeypatch.delenv("WP_APP_PASSWORD", raising=False)
    importlib.reload(main_module)
