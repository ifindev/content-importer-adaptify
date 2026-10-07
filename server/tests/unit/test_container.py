from unittest.mock import patch

import pytest

from app.adapters.testing.in_memory_repository import InMemoryArticleRepository
from app.container import build_container
from app.settings import Settings

TEST_ENCRYPTION_KEY = "YSjz2DgMl1sA6FQXgBgf0bEtqYv-iSSAh6cqs5YC1nQ="


def _settings(app_env: str) -> Settings:
    return Settings(app_env=app_env, credential_encryption_key=TEST_ENCRYPTION_KEY)


def test_falls_back_to_in_memory_when_firestore_unavailable_locally():
    with patch("app.container.firestore.Client", side_effect=RuntimeError("no creds")):
        container = build_container(_settings("local"))

    assert container.firestore_client is None
    assert isinstance(container.repository_for("site-a"), InMemoryArticleRepository)


def test_falls_back_to_in_memory_when_firestore_unavailable_in_test_env():
    with patch("app.container.firestore.Client", side_effect=RuntimeError("no creds")):
        container = build_container(_settings("test"))

    assert container.firestore_client is None
    assert isinstance(container.repository_for("site-a"), InMemoryArticleRepository)


def test_raises_when_firestore_unavailable_in_gcp():
    with patch("app.container.firestore.Client", side_effect=RuntimeError("no creds")):
        with pytest.raises(RuntimeError):
            build_container(_settings("gcp"))


def test_repository_for_reuses_the_same_in_memory_instance_per_site():
    with patch("app.container.firestore.Client", side_effect=RuntimeError("no creds")):
        container = build_container(_settings("local"))

    first = container.repository_for("site-a")
    second = container.repository_for("site-a")
    other = container.repository_for("site-b")

    assert first is second
    assert first is not other
