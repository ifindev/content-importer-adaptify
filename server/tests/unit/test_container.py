from unittest.mock import patch

import pytest

from app.adapters.testing.in_memory_repository import InMemoryArticleRepository
from app.container import build_container
from app.settings import Settings


def _settings(app_env: str) -> Settings:
    return Settings(app_env=app_env)


def test_falls_back_to_in_memory_when_firestore_unavailable_locally():
    with patch("app.container.firestore.Client", side_effect=RuntimeError("no creds")):
        container = build_container(_settings("local"))

    assert isinstance(container.article_repository, InMemoryArticleRepository)


def test_falls_back_to_in_memory_when_firestore_unavailable_in_test_env():
    with patch("app.container.firestore.Client", side_effect=RuntimeError("no creds")):
        container = build_container(_settings("test"))

    assert isinstance(container.article_repository, InMemoryArticleRepository)


def test_raises_when_firestore_unavailable_in_gcp():
    with patch("app.container.firestore.Client", side_effect=RuntimeError("no creds")):
        with pytest.raises(RuntimeError):
            build_container(_settings("gcp"))
