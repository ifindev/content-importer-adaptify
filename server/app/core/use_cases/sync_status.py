from dataclasses import dataclass
from datetime import datetime

from app.core.domain import lifecycle
from app.core.domain.errors import WordPressError
from app.core.domain.models import Article, PostStatus
from app.core.domain.statuses import EventType, Status, SyncWarning
from app.core.ports.article_repository import ArticleRepository
from app.core.ports.clock import Clock
from app.core.ports.publisher import Publisher

CACHE_TTL_SECONDS = 60
PUBLISHED_RECHECK_SECONDS = 24 * 60 * 60
SYNC_ACTOR = "system"


@dataclass
class SyncResult:
    unreachable: bool


class SyncCache:
    """TTL cache, one entry per site, single process.

    ponytail: swap for a shared cache (Redis etc.) if this ever runs multi-process.
    """

    def __init__(self) -> None:
        self._entries: dict[str, tuple[datetime, SyncResult]] = {}

    def get(self, site_id: str, now: datetime) -> SyncResult | None:
        entry = self._entries.get(site_id)
        if entry is None:
            return None
        cached_at, result = entry
        if (now - cached_at).total_seconds() >= CACHE_TTL_SECONDS:
            return None
        return result

    def set(self, site_id: str, now: datetime, result: SyncResult) -> None:
        self._entries[site_id] = (now, result)


def map_wp_status(
    our_status: Status, wp_result: PostStatus | None, now: datetime
) -> tuple[Status | None, SyncWarning | None]:
    if wp_result is None:
        return None, SyncWarning.MISSING_IN_WORDPRESS
    if wp_result.status == "publish":
        if our_status == Status.SCHEDULED:
            return Status.PUBLISHED, None
        return None, None
    if wp_result.status == "future":
        if wp_result.date_gmt is not None and wp_result.date_gmt <= now:
            return None, SyncWarning.LATE
        return None, None
    return None, SyncWarning.CHANGED_IN_WORDPRESS


def _needs_recheck(article: Article, now: datetime) -> bool:
    return (
        article.last_checked_at is None
        or (now - article.last_checked_at).total_seconds() >= PUBLISHED_RECHECK_SECONDS
    )


async def sync_statuses(
    repository: ArticleRepository,
    publisher: Publisher,
    clock: Clock,
    cache: SyncCache,
    *,
    site_id: str,
) -> SyncResult:
    now = clock.now()
    cached = cache.get(site_id, now)
    if cached is not None:
        return cached

    scheduled = repository.list_articles(status=Status.SCHEDULED)
    stale_published = [
        a for a in repository.list_articles(status=Status.PUBLISHED) if _needs_recheck(a, now)
    ]
    checkable = [a for a in scheduled + stale_published if a.wp_post_id is not None]

    if not checkable:
        result = SyncResult(unreachable=False)
        cache.set(site_id, now, result)
        return result

    try:
        statuses = await publisher.get_statuses([a.wp_post_id for a in checkable if a.wp_post_id])
    except WordPressError:
        result = SyncResult(unreachable=True)
        cache.set(site_id, now, result)
        return result

    by_id = {s.id: s for s in statuses}
    for article in checkable:
        wp_result = by_id.get(article.wp_post_id)
        new_status, warning = map_wp_status(article.status, wp_result, now)
        if new_status is not None:
            updated, event = lifecycle.transition(
                article, new_status, SYNC_ACTOR, EventType.PUBLISHED, now
            )
            updated = updated.model_copy(
                update={
                    "published_url": wp_result.link if wp_result else None,
                    "sync_warning": None,
                    "last_checked_at": now,
                }
            )
            repository.save_article(updated, event)
        else:
            repository.save_article(
                article.model_copy(update={"sync_warning": warning, "last_checked_at": now})
            )

    result = SyncResult(unreachable=False)
    cache.set(site_id, now, result)
    return result
