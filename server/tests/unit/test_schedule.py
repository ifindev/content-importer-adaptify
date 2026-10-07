from datetime import UTC, datetime, timedelta

import pytest

from app.adapters.testing.clock import FixedClock
from app.adapters.testing.in_memory_repository import InMemoryArticleRepository
from app.adapters.testing.scripted_publisher import ScriptedPublisher
from app.core.domain.errors import (
    NotFailedError,
    NotSchedulableError,
    PublishAtInPastError,
    WordPressError,
)
from app.core.domain.models import Article
from app.core.domain.statuses import Status
from app.core.use_cases.schedule import retry, schedule

pytestmark = pytest.mark.anyio

NOW = datetime(2026, 10, 7, 12, 0, 0, tzinfo=UTC)
FUTURE = NOW + timedelta(days=1)

NOT_SCHEDULABLE = [
    Status.DRAFT,
    Status.AWAITING_APPROVAL,
    Status.CHANGES_REQUESTED,
    Status.PUBLISHED,
    Status.FAILED,
]


def _article(
    status: Status,
    wp_post_id: int | None = None,
    publish_at_utc: datetime | None = None,
) -> Article:
    return Article(
        id="a1",
        title="Title",
        slug="title",
        body_html="<p>hi</p>",
        source="paste",
        status=status,
        version=1,
        wp_post_id=wp_post_id,
        publish_at_utc=publish_at_utc,
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


async def test_schedule_creates_a_new_post_from_approved(repository, clock, publisher):
    article = _article(Status.APPROVED)
    repository.create_article(article)

    updated = await schedule(article, FUTURE, repository, publisher, clock, "agency")

    assert updated.status == Status.SCHEDULED
    assert updated.wp_post_id == 1
    assert updated.publish_at_utc == FUTURE
    assert publisher.created == [
        {"title": "Title", "slug": "title", "html": "<p>hi</p>", "publish_at_utc": FUTURE}
    ]
    events = repository.list_events("a1")
    assert events[-1].type.value == "scheduled"
    assert events[-1].actor == "agency"


async def test_schedule_date_only_change_from_scheduled(repository, clock, publisher):
    article = _article(Status.SCHEDULED, wp_post_id=42, publish_at_utc=NOW)
    repository.create_article(article)

    updated = await schedule(article, FUTURE, repository, publisher, clock, "agency")

    assert updated.status == Status.SCHEDULED
    assert updated.publish_at_utc == FUTURE
    assert publisher.updated == [
        {
            "wp_post_id": 42,
            "title": None,
            "slug": None,
            "html": None,
            "publish_at_utc": FUTURE,
            "status": None,
        }
    ]
    events = repository.list_events("a1")
    assert events[-1].type.value == "date_changed"


async def test_schedule_full_reschedule_from_approved_with_existing_post(
    repository, clock, publisher
):
    article = _article(Status.APPROVED, wp_post_id=42, publish_at_utc=NOW)
    repository.create_article(article)

    updated = await schedule(article, FUTURE, repository, publisher, clock, "agency")

    assert updated.status == Status.SCHEDULED
    assert publisher.updated == [
        {
            "wp_post_id": 42,
            "title": "Title",
            "slug": "title",
            "html": "<p>hi</p>",
            "publish_at_utc": FUTURE,
            "status": "future",
        }
    ]
    events = repository.list_events("a1")
    assert events[-1].type.value == "scheduled"


@pytest.mark.parametrize("status", NOT_SCHEDULABLE)
async def test_schedule_refused_from_other_statuses(status, repository, clock, publisher):
    article = _article(status)
    repository.create_article(article)

    with pytest.raises(NotSchedulableError):
        await schedule(article, FUTURE, repository, publisher, clock, "agency")


async def test_schedule_refuses_a_past_publish_at(repository, clock, publisher):
    article = _article(Status.APPROVED)
    repository.create_article(article)

    with pytest.raises(PublishAtInPastError):
        await schedule(article, NOW - timedelta(seconds=1), repository, publisher, clock, "agency")


async def test_schedule_refuses_publish_at_equal_to_now(repository, clock, publisher):
    article = _article(Status.APPROVED)
    repository.create_article(article)

    with pytest.raises(PublishAtInPastError):
        await schedule(article, NOW, repository, publisher, clock, "agency")


async def test_schedule_create_timeout_recovers_via_slug_lookup(repository, clock, publisher):
    article = _article(Status.APPROVED)
    repository.create_article(article)
    publisher.create_error = WordPressError(0, "transport_error", "timed out")
    publisher.find_by_slug_result = 99

    updated = await schedule(article, FUTURE, repository, publisher, clock, "agency")

    assert updated.status == Status.SCHEDULED
    assert updated.wp_post_id == 99
    assert publisher.find_by_slug_calls == ["title"]


async def test_schedule_create_timeout_with_no_slug_match_fails(repository, clock, publisher):
    article = _article(Status.APPROVED)
    repository.create_article(article)
    publisher.create_error = WordPressError(0, "transport_error", "timed out")
    publisher.find_by_slug_result = None

    with pytest.raises(WordPressError):
        await schedule(article, FUTURE, repository, publisher, clock, "agency")

    saved = repository.get_article("a1")
    assert saved.status == Status.FAILED
    assert saved.last_error is not None
    events = repository.list_events("a1")
    assert events[-1].type.value == "failed"


async def test_schedule_create_non_timeout_error_fails_without_slug_lookup(
    repository, clock, publisher
):
    article = _article(Status.APPROVED)
    repository.create_article(article)
    publisher.create_error = WordPressError(400, "invalid_slug", "bad slug")

    with pytest.raises(WordPressError):
        await schedule(article, FUTURE, repository, publisher, clock, "agency")

    assert publisher.find_by_slug_calls == []
    saved = repository.get_article("a1")
    assert saved.status == Status.FAILED


async def test_retry_only_from_failed(repository, clock, publisher):
    article = _article(Status.APPROVED)
    repository.create_article(article)

    with pytest.raises(NotFailedError):
        await retry(article, repository, publisher, clock, "agency")


async def test_retry_from_failed_without_post_id_creates(repository, clock, publisher):
    article = _article(Status.FAILED, publish_at_utc=FUTURE)
    repository.create_article(article)

    updated = await retry(article, repository, publisher, clock, "agency")

    assert updated.status == Status.SCHEDULED
    assert updated.wp_post_id == 1
    events = repository.list_events("a1")
    assert events[-1].type.value == "retried"


async def test_retry_from_failed_with_post_id_updates(repository, clock, publisher):
    article = _article(Status.FAILED, wp_post_id=42, publish_at_utc=FUTURE)
    repository.create_article(article)

    updated = await retry(article, repository, publisher, clock, "agency")

    assert updated.status == Status.SCHEDULED
    assert publisher.updated[0]["wp_post_id"] == 42
    events = repository.list_events("a1")
    assert events[-1].type.value == "retried"


async def test_retry_can_fail_again(repository, clock, publisher):
    article = _article(Status.FAILED, publish_at_utc=FUTURE)
    repository.create_article(article)
    publisher.create_error = WordPressError(500, "server_error", "oops")

    with pytest.raises(WordPressError):
        await retry(article, repository, publisher, clock, "agency")

    saved = repository.get_article("a1")
    assert saved.status == Status.FAILED
