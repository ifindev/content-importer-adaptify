from app.core.domain.report import (
    Report,
    avg_approval_seconds,
    avg_change_rounds,
    change_rounds,
    needs_attention,
    published,
    published_this_month,
    status_counts,
    upcoming,
)
from app.core.ports.article_repository import ArticleRepository
from app.core.ports.clock import Clock
from app.core.ports.publisher import Publisher
from app.core.use_cases.sync_status import SyncCache, sync_statuses


async def build_report(
    repository: ArticleRepository,
    publisher: Publisher,
    clock: Clock,
    cache: SyncCache,
    *,
    site_id: str,
) -> tuple[Report, bool]:
    sync_result = await sync_statuses(repository, publisher, clock, cache, site_id=site_id)
    articles = repository.list_articles()
    events_by_article = {a.id: repository.list_events(a.id) for a in articles}
    now = clock.now()
    rounds = change_rounds(articles, events_by_article)

    report = Report(
        status_counts=status_counts(articles),
        published_this_month=published_this_month(articles, events_by_article, now),
        avg_approval_seconds=avg_approval_seconds(articles, events_by_article),
        change_rounds=rounds,
        avg_change_rounds=avg_change_rounds(articles, rounds),
        upcoming=upcoming(articles),
        published=published(articles, events_by_article),
        needs_attention=needs_attention(articles),
    )
    return report, sync_result.unreachable
