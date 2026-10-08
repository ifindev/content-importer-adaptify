import logging
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest

from app.adapters.testing.clock import FixedClock
from app.adapters.testing.in_memory_repository import InMemoryArticleRepository
from app.adapters.wordpress.publisher import WordPressPublisher
from app.core.domain.models import Article
from app.core.domain.statuses import Status, SyncWarning
from app.core.use_cases.sync_status import SyncCache, sync_statuses
from app.settings import Settings

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


@pytest.fixture
def settings() -> Settings:
    return Settings()


@pytest.fixture
def publisher(settings: Settings) -> WordPressPublisher:
    return WordPressPublisher(settings.wp_base_url, settings.wp_username, settings.wp_app_password)


def _raw_client(settings: Settings) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=f"{settings.wp_base_url}/wp-json/wp/v2",
        auth=httpx.BasicAuth(settings.wp_username, settings.wp_app_password),
    )


async def _delete_post(settings: Settings, post_id: int) -> None:
    async with _raw_client(settings) as client:
        deleted = await client.delete(f"/posts/{post_id}", params={"force": "true"})
    logger.info("DELETE /posts/%s -> %s", post_id, deleted.status_code)


async def test_sync_detects_post_changed_to_draft(
    settings: Settings, publisher: WordPressPublisher
):
    html = (Path(__file__).parent.parent / "fixtures" / "sample_article.html").read_text()
    slug = f"t-021-changed-in-wordpress-{uuid.uuid4()}"
    publish_at = datetime.now(UTC) + timedelta(hours=1)
    post_id = await publisher.create_scheduled("T-021 sync changed", slug, html, publish_at)

    try:
        async with _raw_client(settings) as client:
            response = await client.post(f"/posts/{post_id}", json={"status": "draft"})
            response.raise_for_status()

        now = datetime.now(UTC)
        repository = InMemoryArticleRepository()
        article = Article(
            id="a1",
            title="T-021 sync changed",
            slug=slug,
            body_html=html,
            source="paste",
            status=Status.SCHEDULED,
            version=1,
            wp_post_id=post_id,
            publish_at_utc=publish_at,
            created_at=now,
            updated_at=now,
        )
        repository.create_article(article)

        result = await sync_statuses(
            repository, publisher, FixedClock(now), SyncCache(), site_id="s1"
        )

        assert result.unreachable is False
        updated = repository.get_article("a1")
        assert updated.status == Status.SCHEDULED
        assert updated.sync_warning == SyncWarning.CHANGED_IN_WORDPRESS
    finally:
        await _delete_post(settings, post_id)
