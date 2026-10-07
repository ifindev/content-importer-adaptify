import logging
import time
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest

from app.adapters.testing.clock import FixedClock
from app.adapters.testing.in_memory_repository import InMemoryArticleRepository
from app.adapters.wordpress.publisher import WordPressPublisher
from app.core.domain.models import Article
from app.core.domain.statuses import Status
from app.core.use_cases.edit_article import edit_article
from app.settings import Settings

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


class _UnusedParser:
    def clean_html(self, html: str):
        raise NotImplementedError("body_html is not edited in these tests")


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


async def test_update_scheduled_changes_the_date(settings: Settings, publisher: WordPressPublisher):
    html = (Path(__file__).parent.parent / "fixtures" / "sample_article.html").read_text()
    slug = f"t-020-update-date-{uuid.uuid4()}"
    publish_at = datetime.now(UTC) + timedelta(hours=1)
    post_id = await publisher.create_scheduled("T-020 update date", slug, html, publish_at)

    try:
        new_publish_at = publish_at + timedelta(hours=1)
        await publisher.update_scheduled(post_id, publish_at_utc=new_publish_at)

        async with _raw_client(settings) as client:
            response = await client.get(f"/posts/{post_id}", params={"context": "edit"})
            response.raise_for_status()
            data = response.json()

        assert data["status"] == "future"
        got = datetime.fromisoformat(data["date_gmt"]).replace(tzinfo=UTC)
        assert abs((got - new_publish_at).total_seconds()) < 2
    finally:
        await _delete_post(settings, post_id)


async def test_update_scheduled_full_reschedule(settings: Settings, publisher: WordPressPublisher):
    html = (Path(__file__).parent.parent / "fixtures" / "sample_article.html").read_text()
    slug = f"t-020-reschedule-{uuid.uuid4()}"
    publish_at = datetime.now(UTC) + timedelta(hours=1)
    post_id = await publisher.create_scheduled("Original title", slug, html, publish_at)

    try:
        new_publish_at = publish_at + timedelta(hours=1)
        await publisher.update_scheduled(
            post_id,
            title="New title",
            slug=slug,
            html=html,
            publish_at_utc=new_publish_at,
            status="future",
        )

        async with _raw_client(settings) as client:
            response = await client.get(f"/posts/{post_id}", params={"context": "edit"})
            response.raise_for_status()
            data = response.json()

        assert data["status"] == "future"
        assert data["title"]["raw"] == "New title"
    finally:
        await _delete_post(settings, post_id)


async def test_set_draft_moves_a_scheduled_post_to_draft(
    settings: Settings, publisher: WordPressPublisher
):
    html = (Path(__file__).parent.parent / "fixtures" / "sample_article.html").read_text()
    slug = f"t-020-set-draft-{uuid.uuid4()}"
    publish_at = datetime.now(UTC) + timedelta(hours=1)
    post_id = await publisher.create_scheduled("T-020 set draft", slug, html, publish_at)

    try:
        await publisher.set_draft(post_id)

        async with _raw_client(settings) as client:
            response = await client.get(f"/posts/{post_id}", params={"context": "edit"})
            response.raise_for_status()
            data = response.json()

        assert data["status"] == "draft"
    finally:
        await _delete_post(settings, post_id)


async def test_find_by_slug_finds_an_existing_post(
    settings: Settings, publisher: WordPressPublisher
):
    html = (Path(__file__).parent.parent / "fixtures" / "sample_article.html").read_text()
    slug = f"t-020-find-by-slug-{uuid.uuid4()}"
    publish_at = datetime.now(UTC) + timedelta(hours=1)
    post_id = await publisher.create_scheduled("T-020 find by slug", slug, html, publish_at)

    try:
        found = await publisher.find_by_slug(slug)
        assert found == post_id
    finally:
        await _delete_post(settings, post_id)


async def test_find_by_slug_returns_none_when_not_found(
    settings: Settings, publisher: WordPressPublisher
):
    found = await publisher.find_by_slug(f"t-020-does-not-exist-{uuid.uuid4()}")
    assert found is None


async def test_edit_article_moves_scheduled_wordpress_post_to_draft(
    settings: Settings, publisher: WordPressPublisher
):
    html = (Path(__file__).parent.parent / "fixtures" / "sample_article.html").read_text()
    slug = f"t-020-edit-draft-{uuid.uuid4()}"
    publish_at = datetime.now(UTC) + timedelta(hours=1)
    post_id = await publisher.create_scheduled("T-020 edit draft", slug, html, publish_at)

    try:
        now = datetime.now(UTC)
        repository = InMemoryArticleRepository()
        article = Article(
            id="a1",
            title="T-020 edit draft",
            slug=slug,
            body_html=html,
            source="paste",
            status=Status.SCHEDULED,
            version=1,
            wp_post_id=post_id,
            created_at=now,
            updated_at=now,
        )
        repository.create_article(article)

        await edit_article(
            article,
            "New title",
            None,
            None,
            repository,
            _UnusedParser(),
            FixedClock(now),
            publisher,
            "agency",
        )

        async with _raw_client(settings) as client:
            response = await client.get(f"/posts/{post_id}", params={"context": "edit"})
            response.raise_for_status()
            data = response.json()

        assert data["status"] == "draft"
        assert repository.get_article("a1").status == Status.DRAFT
    finally:
        await _delete_post(settings, post_id)
