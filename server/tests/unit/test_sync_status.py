from datetime import UTC, datetime, timedelta

import pytest

from app.adapters.testing.clock import FixedClock
from app.adapters.testing.in_memory_repository import InMemoryArticleRepository
from app.adapters.testing.scripted_publisher import ScriptedPublisher
from app.core.domain.errors import WordPressError
from app.core.domain.models import Article, PostStatus
from app.core.domain.statuses import EventType, Status, SyncWarning
from app.core.use_cases.sync_status import PUBLISHED_RECHECK_SECONDS, SyncCache, sync_statuses

pytestmark = pytest.mark.anyio

NOW = datetime(2026, 10, 7, 12, 0, 0, tzinfo=UTC)
PAST = NOW - timedelta(hours=1)
FUTURE = NOW + timedelta(hours=1)


def _article(
    article_id: str,
    status: Status,
    wp_post_id: int | None = 1,
    last_checked_at: datetime | None = None,
) -> Article:
    return Article(
        id=article_id,
        title="Title",
        slug=article_id,
        body_html="<p>hi</p>",
        source="paste",
        status=status,
        version=1,
        wp_post_id=wp_post_id,
        last_checked_at=last_checked_at,
        created_at=NOW,
        updated_at=NOW,
    )


@pytest.fixture
def repository():
    return InMemoryArticleRepository()


@pytest.fixture
def clock():
    return FixedClock(NOW)


@pytest.fixture
def publisher():
    return ScriptedPublisher()


@pytest.fixture
def cache():
    return SyncCache()


async def test_publish_result_transitions_scheduled_to_published(
    repository, clock, publisher, cache
):
    repository.create_article(_article("a1", Status.SCHEDULED, wp_post_id=1))
    publisher.get_statuses_result = [
        PostStatus(id=1, status="publish", link="https://example.com/a1", date_gmt=PAST)
    ]

    result = await sync_statuses(repository, publisher, clock, cache)

    assert result.unreachable is False
    updated = repository.get_article("a1")
    assert updated.status == Status.PUBLISHED
    assert updated.published_url == "https://example.com/a1"
    assert updated.sync_warning is None
    events = repository.list_events("a1")
    assert events[-1].type == EventType.PUBLISHED


async def test_future_but_passed_shows_late_without_changing_status(
    repository, clock, publisher, cache
):
    repository.create_article(_article("a1", Status.SCHEDULED, wp_post_id=1))
    publisher.get_statuses_result = [PostStatus(id=1, status="future", link=None, date_gmt=PAST)]

    await sync_statuses(repository, publisher, clock, cache)

    updated = repository.get_article("a1")
    assert updated.status == Status.SCHEDULED
    assert updated.sync_warning == SyncWarning.LATE


async def test_future_ahead_has_no_warning(repository, clock, publisher, cache):
    repository.create_article(_article("a1", Status.SCHEDULED, wp_post_id=1))
    publisher.get_statuses_result = [PostStatus(id=1, status="future", link=None, date_gmt=FUTURE)]

    await sync_statuses(repository, publisher, clock, cache)

    updated = repository.get_article("a1")
    assert updated.status == Status.SCHEDULED
    assert updated.sync_warning is None


@pytest.mark.parametrize("wp_status", ["draft", "private"])
async def test_draft_or_private_shows_changed_without_changing_status(
    repository, clock, publisher, cache, wp_status
):
    repository.create_article(_article("a1", Status.SCHEDULED, wp_post_id=1))
    publisher.get_statuses_result = [PostStatus(id=1, status=wp_status, link=None, date_gmt=None)]

    await sync_statuses(repository, publisher, clock, cache)

    updated = repository.get_article("a1")
    assert updated.status == Status.SCHEDULED
    assert updated.sync_warning == SyncWarning.CHANGED_IN_WORDPRESS


async def test_missing_from_reply_shows_missing_without_changing_status(
    repository, clock, publisher, cache
):
    repository.create_article(_article("a1", Status.SCHEDULED, wp_post_id=1))
    publisher.get_statuses_result = []

    await sync_statuses(repository, publisher, clock, cache)

    updated = repository.get_article("a1")
    assert updated.status == Status.SCHEDULED
    assert updated.sync_warning == SyncWarning.MISSING_IN_WORDPRESS


async def test_wordpress_failure_changes_nothing_and_flags_unreachable(
    repository, clock, publisher, cache
):
    article = _article("a1", Status.SCHEDULED, wp_post_id=1)
    repository.create_article(article)
    publisher.get_statuses_error = WordPressError(503, "unavailable")

    result = await sync_statuses(repository, publisher, clock, cache)

    assert result.unreachable is True
    assert repository.get_article("a1") == article


async def test_cache_hit_within_ttl_calls_publisher_once(repository, clock, publisher, cache):
    repository.create_article(_article("a1", Status.SCHEDULED, wp_post_id=1))
    publisher.get_statuses_result = [PostStatus(id=1, status="future", link=None, date_gmt=FUTURE)]
    calls = []
    original = publisher.get_statuses

    async def _tracked(post_ids):
        calls.append(post_ids)
        return await original(post_ids)

    publisher.get_statuses = _tracked

    await sync_statuses(repository, publisher, clock, cache)
    await sync_statuses(repository, publisher, clock, cache)

    assert len(calls) == 1


async def test_published_recheck_throttle(repository, clock, publisher, cache):
    just_checked = _article("fresh", Status.PUBLISHED, wp_post_id=1, last_checked_at=NOW)
    stale = _article(
        "stale",
        Status.PUBLISHED,
        wp_post_id=2,
        last_checked_at=NOW - timedelta(seconds=PUBLISHED_RECHECK_SECONDS + 1),
    )
    repository.create_article(just_checked)
    repository.create_article(stale)
    publisher.get_statuses_result = [PostStatus(id=2, status="publish", link=None, date_gmt=PAST)]

    await sync_statuses(repository, publisher, clock, cache)

    assert repository.get_article("fresh").last_checked_at == NOW
    assert repository.get_article("stale").last_checked_at == NOW


async def test_no_checkable_articles_skips_wordpress_call(repository, clock, publisher, cache):
    async def _fail(post_ids):
        raise AssertionError("get_statuses should not be called")

    publisher.get_statuses = _fail

    result = await sync_statuses(repository, publisher, clock, cache)

    assert result.unreachable is False
