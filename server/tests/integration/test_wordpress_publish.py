import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest

from app.adapters.wordpress.publisher import WordPressPublisher
from app.settings import Settings

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


@pytest.fixture
def settings() -> Settings:
    return Settings()


@pytest.fixture
def publisher(settings: Settings) -> WordPressPublisher:
    return WordPressPublisher(settings.wp_base_url, settings.wp_username, settings.wp_app_password)


async def test_publish_flow(settings: Settings, publisher: WordPressPublisher):
    html = (Path(__file__).parent.parent / "fixtures" / "sample_article.html").read_text()
    publish_at = datetime.now(UTC) + timedelta(seconds=3)

    post_id = await publisher.create_scheduled(
        "T-009 Integration Test", "t-009-integration-test", html, publish_at
    )

    try:
        time.sleep(4)
        async with httpx.AsyncClient() as client:
            await client.get(f"{settings.wp_base_url}/wp-cron.php")

        statuses = await publisher.get_statuses([post_id])
        assert len(statuses) == 1
        assert statuses[0].status == "publish"
        assert statuses[0].link

        async with httpx.AsyncClient(
            base_url=f"{settings.wp_base_url}/wp-json/wp/v2",
            auth=httpx.BasicAuth(settings.wp_username, settings.wp_app_password),
        ) as client:
            response = await client.get(f"/posts/{post_id}", params={"context": "edit"})
            response.raise_for_status()
            assert html.strip() in response.json()["content"]["raw"]
    finally:
        async with httpx.AsyncClient(
            base_url=f"{settings.wp_base_url}/wp-json/wp/v2",
            auth=httpx.BasicAuth(settings.wp_username, settings.wp_app_password),
        ) as client:
            await client.delete(f"/posts/{post_id}", params={"force": "true"})
