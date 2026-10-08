import json
from datetime import UTC, datetime

import httpx
import pytest

from app.adapters.wordpress.publisher import WordPressPublisher
from app.core.domain.errors import WordPressError

pytestmark = pytest.mark.anyio


def _publisher(handler) -> WordPressPublisher:
    return WordPressPublisher(
        "http://wp.test", "admin", "app-pass", transport=httpx.MockTransport(handler)
    )


async def test_check_credentials_ok():
    def handler(request):
        assert request.url.path == "/wp-json/wp/v2/users/me"
        assert request.url.params["context"] == "edit"
        return httpx.Response(200, json={"id": 1})

    await _publisher(handler).check_credentials()


async def test_check_credentials_bad_password():
    def handler(request):
        return httpx.Response(401, json={"code": "incorrect_password", "message": "Bad password."})

    with pytest.raises(WordPressError) as exc_info:
        await _publisher(handler).check_credentials()
    assert exc_info.value.http_status == 401
    assert exc_info.value.code == "incorrect_password"


async def test_create_scheduled_request_shape():
    captured = {}

    def handler(request):
        captured["body"] = request.read()
        return httpx.Response(201, json={"id": 42})

    publish_at = datetime(2026, 10, 6, 10, 0, 0, tzinfo=UTC)
    post_id = await _publisher(handler).create_scheduled("Title", "slug", "<p>html</p>", publish_at)

    assert post_id == 42
    body = json.loads(captured["body"])
    assert body == {
        "title": "Title",
        "slug": "slug",
        "content": "<p>html</p>",
        "status": "future",
        "date_gmt": "2026-10-06T10:00:00",
    }


async def test_get_statuses_parses_response():
    def handler(request):
        assert request.url.params["include"] == "12,15"
        assert request.url.params["status"] == "publish,future,draft,private"
        return httpx.Response(
            200,
            json=[
                {
                    "id": 12,
                    "status": "publish",
                    "link": "http://x/p",
                    "date_gmt": "2026-10-06T10:00:00",
                },
                {"id": 15, "status": "future", "link": None, "date_gmt": "2026-10-07T00:00:00"},
            ],
        )

    statuses = await _publisher(handler).get_statuses([12, 15])
    assert statuses[0].id == 12
    assert statuses[0].status == "publish"
    assert statuses[0].link == "http://x/p"
    assert statuses[1].link is None


async def test_get_statuses_asks_in_chunks_of_100():
    asked: list[list[int]] = []

    def handler(request):
        ids = [int(i) for i in request.url.params["include"].split(",")]
        asked.append(ids)
        posts = [{"id": i, "status": "future", "link": None, "date_gmt": None} for i in ids]
        return httpx.Response(200, json=posts)

    statuses = await _publisher(handler).get_statuses(list(range(1, 151)))

    assert [len(chunk) for chunk in asked] == [100, 50]
    assert len(statuses) == 150
