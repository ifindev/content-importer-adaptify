from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.adapters.testing.clock import FixedClock
from app.adapters.testing.in_memory_repository import InMemoryArticleRepository
from app.adapters.testing.scripted_publisher import ScriptedPublisher
from app.api.auth import require_session
from app.api.deps import SiteContext, get_clock, get_document_parser, get_site_context
from app.api.main import app
from app.core.domain.models import Site

NOW = datetime(2026, 10, 7, 12, 0, 0, tzinfo=UTC)
SITE_ID = "s1"

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture
def repository():
    return InMemoryArticleRepository()


@pytest.fixture
def client(repository):
    from app.adapters.documents.parser import RealDocumentParser

    site_context = SiteContext(
        site_id=SITE_ID,
        site=Site(id=SITE_ID, name="Test site", wp_base_url="http://wp.test"),
        repository=repository,
        publisher=ScriptedPublisher(),
    )
    app.dependency_overrides[require_session] = lambda: "test-uid"
    app.dependency_overrides[get_site_context] = lambda: site_context
    app.dependency_overrides[get_document_parser] = lambda: RealDocumentParser()
    app.dependency_overrides[get_clock] = lambda: FixedClock(NOW)
    yield TestClient(app)
    app.dependency_overrides.clear()


def _docx_file(name: str) -> tuple[str, bytes, str]:
    content = (FIXTURES / name).read_bytes()
    return (
        name,
        content,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


def test_paste_creates_draft_article(client):
    response = client.post(
        f"/sites/{SITE_ID}/articles/paste", json={"html": "<h1>Title</h1><p>Body</p>"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "draft"
    assert body["title"] == "Title"
    assert body["source"] == "paste"


def test_paste_with_image_warns_and_strips_it(client):
    response = client.post(
        f"/sites/{SITE_ID}/articles/paste", json={"html": "<h1>T</h1><p>body</p><img src='x.png'>"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["warnings"]
    assert "img" not in body["body_html"]


def test_paste_empty_after_cleaning_returns_422(client):
    response = client.post(f"/sites/{SITE_ID}/articles/paste", json={"html": "<img src='x.png'>"})
    assert response.status_code == 422
    assert response.json() == {"code": "empty_content"}


def test_paste_over_size_cap_returns_413(client):
    huge = "<p>" + ("a" * (2 * 1024 * 1024 + 1)) + "</p>"
    response = client.post(f"/sites/{SITE_ID}/articles/paste", json={"html": huge})
    assert response.status_code == 413
    assert response.json() == {"code": "payload_too_large"}


def test_upload_two_valid_files_creates_two_articles(client):
    response = client.post(
        f"/sites/{SITE_ID}/articles/upload",
        files=[
            ("files", _docx_file("heading_simple.docx")),
            ("files", _docx_file("with_table.docx")),
        ],
    )
    assert response.status_code == 201
    results = response.json()["results"]
    assert len(results) == 2
    assert all(r["ok"] for r in results)
    titles = {r["article"]["title"] for r in results}
    assert titles == {"Fixture Title", "Document With Table"}


def test_upload_corrupt_file_fails_only_that_file(client):
    response = client.post(
        f"/sites/{SITE_ID}/articles/upload",
        files=[
            ("files", _docx_file("heading_simple.docx")),
            ("files", _docx_file("corrupt.docx")),
        ],
    )
    assert response.status_code == 201
    results = response.json()["results"]
    by_name = {r["filename"]: r for r in results}
    assert by_name["heading_simple.docx"]["ok"] is True
    assert by_name["corrupt.docx"] == {
        "filename": "corrupt.docx",
        "ok": False,
        "article": None,
        "code": "unreadable_file",
        "warnings": [],
    }


def test_upload_returns_per_file_warnings(client):
    response = client.post(
        f"/sites/{SITE_ID}/articles/upload", files=[("files", _docx_file("with_image.docx"))]
    )
    result = response.json()["results"][0]
    assert result["ok"] is True
    assert result["warnings"]


def test_upload_realistic_article_end_to_end(client):
    response = client.post(
        f"/sites/{SITE_ID}/articles/upload", files=[("files", _docx_file("realistic_article.docx"))]
    )
    assert response.status_code == 201
    result = response.json()["results"][0]
    assert result["ok"] is True
    assert result["article"]["title"] == "How Remote Work Is Reshaping Modern Teams"

    detail = client.get(f"/sites/{SITE_ID}/articles/{result['article']['id']}")
    body_html = detail.json()["body_html"]
    assert body_html.count("<h2>") == 4
    assert "<table>" in body_html
    assert "<strong>deliberate</strong>" in body_html


def test_upload_table_file_keeps_table(client):
    response = client.post(
        f"/sites/{SITE_ID}/articles/upload", files=[("files", _docx_file("with_table.docx"))]
    )
    article_id = response.json()["results"][0]["article"]["id"]
    detail = client.get(f"/sites/{SITE_ID}/articles/{article_id}")
    assert "<table>" in detail.json()["body_html"]


def test_upload_no_files_returns_422(client):
    response = client.post(f"/sites/{SITE_ID}/articles/upload", files=[])
    assert response.status_code == 422
    assert response.json() == {"code": "no_files"}


def test_upload_too_many_files_returns_422(client):
    files = [("files", _docx_file("heading_simple.docx")) for _ in range(11)]
    response = client.post(f"/sites/{SITE_ID}/articles/upload", files=files)
    assert response.status_code == 422
    assert response.json() == {"code": "too_many_files"}


def test_upload_file_too_large_is_per_file(client):
    huge = ("huge.docx", b"x" * (10 * 1024 * 1024 + 1), "application/octet-stream")
    response = client.post(
        f"/sites/{SITE_ID}/articles/upload",
        files=[("files", _docx_file("heading_simple.docx")), ("files", huge)],
    )
    assert response.status_code == 201
    results = {r["filename"]: r for r in response.json()["results"]}
    assert results["huge.docx"]["code"] == "file_too_large"
    assert results["heading_simple.docx"]["ok"] is True


def test_upload_unsupported_file_type_is_per_file(client):
    response = client.post(
        f"/sites/{SITE_ID}/articles/upload",
        files=[("files", ("notes.txt", b"hello", "text/plain"))],
    )
    assert response.status_code == 201
    results = response.json()["results"]
    assert results[0]["code"] == "unsupported_file_type"


def test_import_routes_require_session():
    response = TestClient(app).post(f"/sites/{SITE_ID}/articles/paste", json={"html": "<p>x</p>"})
    assert response.status_code == 401
    assert response.json() == {"code": "invalid_token"}
