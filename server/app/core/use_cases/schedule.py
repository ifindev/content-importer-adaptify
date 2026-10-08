import uuid
from datetime import datetime

from app.core.domain import lifecycle
from app.core.domain.errors import (
    NotFailedError,
    NotSchedulableError,
    NotScheduledError,
    PublishAtInPastError,
    WordPressError,
)
from app.core.domain.models import Article, Event
from app.core.domain.statuses import EventType, Status
from app.core.ports.article_repository import ArticleRepository
from app.core.ports.clock import Clock
from app.core.ports.publisher import Publisher

# Failed is here so the agency can pick a new date when the old one passed.
SCHEDULABLE_STATUSES = {Status.APPROVED, Status.SCHEDULED, Status.FAILED}


async def schedule(
    article: Article,
    publish_at: datetime,
    repository: ArticleRepository,
    publisher: Publisher,
    clock: Clock,
    actor: str,
) -> Article:
    if article.status not in SCHEDULABLE_STATUSES:
        raise NotSchedulableError(article.status)
    if publish_at <= clock.now():
        raise PublishAtInPastError
    return await _create_or_update(article, publish_at, repository, publisher, clock, actor)


async def retry(
    article: Article,
    repository: ArticleRepository,
    publisher: Publisher,
    clock: Clock,
    actor: str,
) -> Article:
    if article.status != Status.FAILED:
        raise NotFailedError(article.status)
    # A Failed article keeps the date it was meant to publish on. Once that's
    # past, the agency sets a new one (schedule accepts Failed).
    if article.publish_at_utc is None or article.publish_at_utc <= clock.now():
        raise PublishAtInPastError
    return await _create_or_update(
        article,
        article.publish_at_utc,
        repository,
        publisher,
        clock,
        actor,
        event_type=EventType.RETRIED,
    )


async def unschedule(
    article: Article,
    repository: ArticleRepository,
    publisher: Publisher,
    clock: Clock,
    actor: str,
) -> Article:
    """Scheduled → Approved: the text didn't change, so approval stays. The
    WordPress post goes to WordPress's trash first, so a refusal changes
    nothing."""
    if article.status != Status.SCHEDULED:
        raise NotScheduledError(article.status)
    if article.wp_post_id is not None:
        try:
            await publisher.trash_post(article.wp_post_id)
        except WordPressError as exc:
            # Already deleted in WordPress by hand: nothing left to remove.
            if exc.http_status != 404:
                raise
    updated, event = lifecycle.transition(
        article, Status.APPROVED, actor, EventType.UNSCHEDULED, clock.now()
    )
    # No post id: the next Set date creates a fresh post.
    updated = updated.model_copy(
        update={"publish_at_utc": None, "sync_warning": None, "wp_post_id": None}
    )
    repository.save_article(updated, event)
    return updated


def _move(
    article: Article,
    to_status: Status,
    actor: str,
    event_type: EventType,
    at: datetime,
    data: dict | None = None,
) -> tuple[Article, Event]:
    """lifecycle.transition, except staying in the same status (a date change
    on Scheduled, a retry that fails again) only records the event."""
    if article.status == to_status:
        event = Event(id=str(uuid.uuid4()), type=event_type, actor=actor, at=at, data=data)
        return article.model_copy(update={"updated_at": at}), event
    return lifecycle.transition(article, to_status, actor, event_type, at, data)


async def _create_or_update(
    article: Article,
    publish_at: datetime,
    repository: ArticleRepository,
    publisher: Publisher,
    clock: Clock,
    actor: str,
    event_type: EventType | None = None,
) -> Article:
    now = clock.now()
    try:
        if article.wp_post_id is None:
            wp_post_id = await _create_with_timeout_recovery(article, publish_at, publisher)
            chosen_event_type = event_type or EventType.SCHEDULED
            update = {"wp_post_id": wp_post_id}
        else:
            if article.status == Status.SCHEDULED:
                await publisher.update_scheduled(article.wp_post_id, publish_at_utc=publish_at)
                chosen_event_type = event_type or EventType.DATE_CHANGED
            else:
                # Failed after a date change: the post exists; send the
                # approved text again.
                await publisher.update_scheduled(
                    article.wp_post_id,
                    title=article.title,
                    slug=article.slug,
                    html=article.body_html,
                    publish_at_utc=publish_at,
                    status="future",
                )
                chosen_event_type = event_type or EventType.SCHEDULED
            update = {}
    except WordPressError as exc:
        failed, failed_event = _move(
            article, Status.FAILED, actor, EventType.FAILED, now, data={"error": str(exc)}
        )
        # Keep the requested date so Retry has one.
        failed = failed.model_copy(update={"last_error": str(exc), "publish_at_utc": publish_at})
        repository.save_article(failed, failed_event)
        raise

    updated, event = _move(article, Status.SCHEDULED, actor, chosen_event_type, now)
    updated = updated.model_copy(
        update={**update, "publish_at_utc": publish_at, "last_error": None}
    )
    repository.save_article(updated, event)
    return updated


async def _create_with_timeout_recovery(
    article: Article, publish_at: datetime, publisher: Publisher
) -> int:
    try:
        return await publisher.create_scheduled(
            article.title, article.slug, article.body_html, publish_at
        )
    except WordPressError as exc:
        if exc.code == "transport_error":
            found = await publisher.find_by_slug(article.slug)
            if found is not None:
                return found
        raise
