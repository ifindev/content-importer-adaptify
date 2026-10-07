import uuid
from datetime import datetime

from app.core.domain.errors import (
    NotFailedError,
    NotSchedulableError,
    PublishAtInPastError,
    WordPressError,
)
from app.core.domain.models import Article, Event
from app.core.domain.statuses import EventType, Status
from app.core.ports.article_repository import ArticleRepository
from app.core.ports.clock import Clock
from app.core.ports.publisher import Publisher

SCHEDULABLE_STATUSES = {Status.APPROVED, Status.SCHEDULED}


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
    return await _create_or_update(
        article,
        article.publish_at_utc,
        repository,
        publisher,
        clock,
        actor,
        event_type=EventType.RETRIED,
    )


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
            updated = article.model_copy(
                update={
                    "status": Status.SCHEDULED,
                    "wp_post_id": wp_post_id,
                    "publish_at_utc": publish_at,
                    "last_error": None,
                }
            )
            chosen_event_type = event_type or EventType.SCHEDULED
        elif article.status == Status.SCHEDULED:
            await publisher.update_scheduled(article.wp_post_id, publish_at_utc=publish_at)
            updated = article.model_copy(update={"publish_at_utc": publish_at, "last_error": None})
            chosen_event_type = event_type or EventType.DATE_CHANGED
        else:
            await publisher.update_scheduled(
                article.wp_post_id,
                title=article.title,
                slug=article.slug,
                html=article.body_html,
                publish_at_utc=publish_at,
                status="future",
            )
            updated = article.model_copy(
                update={
                    "status": Status.SCHEDULED,
                    "publish_at_utc": publish_at,
                    "last_error": None,
                }
            )
            chosen_event_type = event_type or EventType.SCHEDULED
    except WordPressError as exc:
        failed = article.model_copy(update={"status": Status.FAILED, "last_error": str(exc)})
        failed_event = Event(
            id=str(uuid.uuid4()),
            type=EventType.FAILED,
            actor=actor,
            at=now,
            data={"error": str(exc)},
        )
        repository.save_article(failed, failed_event)
        raise

    event = Event(id=str(uuid.uuid4()), type=chosen_event_type, actor=actor, at=now)
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
