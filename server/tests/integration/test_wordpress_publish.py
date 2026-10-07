import logging
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest

from app.adapters.wordpress.publisher import WordPressPublisher
from app.settings import Settings

logger = logging.getLogger(__name__)

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
    logger.info("Creating scheduled post for %s", publish_at.isoformat())

    post_id = await publisher.create_scheduled(
        "T-009 Integration Test", "t-009-integration-test", html, publish_at
    )
    logger.info("Created post %s; waiting 4s for its publish time", post_id)

    try:
        time.sleep(4)
        cron_url = f"{settings.wp_base_url}/wp-cron.php"
        logger.info("Triggering %s", cron_url)
        async with httpx.AsyncClient() as client:
            cron = await client.get(cron_url)
        logger.info("wp-cron.php -> %s", cron.status_code)

        statuses = await publisher.get_statuses([post_id])
        assert len(statuses) == 1
        status = statuses[0]
        logger.info("Post %s status=%s link=%s", status.id, status.status, status.link)
        assert status.status == "publish"
        assert status.link

        async with httpx.AsyncClient(
            base_url=f"{settings.wp_base_url}/wp-json/wp/v2",
            auth=httpx.BasicAuth(settings.wp_username, settings.wp_app_password),
        ) as client:
            response = await client.get(f"/posts/{post_id}", params={"context": "edit"})
            logger.info("GET /posts/%s?context=edit -> %s", post_id, response.status_code)
            response.raise_for_status()
            assert html.strip() in response.json()["content"]["raw"]
        logger.info("Post %s HTML matches the sample", post_id)
    finally:
        logger.info("Deleting post %s", post_id)
        async with httpx.AsyncClient(
            base_url=f"{settings.wp_base_url}/wp-json/wp/v2",
            auth=httpx.BasicAuth(settings.wp_username, settings.wp_app_password),
        ) as client:
            deleted = await client.delete(f"/posts/{post_id}", params={"force": "true"})
        logger.info("DELETE /posts/%s -> %s", post_id, deleted.status_code)
