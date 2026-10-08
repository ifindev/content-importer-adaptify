from dataclasses import dataclass
from datetime import datetime

from app.core.domain.models import Article, Event
from app.core.domain.statuses import EventType, Status

EventsByArticle = dict[str, list[Event]]


@dataclass
class ChangeRoundsEntry:
    article_id: str
    title: str
    rounds: int


@dataclass
class UpcomingEntry:
    article_id: str
    title: str
    publish_at_utc: datetime


@dataclass
class PublishedEntry:
    article_id: str
    title: str
    published_url: str
    published_at: datetime


@dataclass
class NeedsAttentionEntry:
    article_id: str
    title: str
    reason: str
    detail: str | None


@dataclass
class Report:
    status_counts: dict[Status, int]
    published_this_month: int
    avg_approval_seconds: float | None
    change_rounds: list[ChangeRoundsEntry]
    avg_change_rounds: float | None
    upcoming: list[UpcomingEntry]
    published: list[PublishedEntry]
    needs_attention: list[NeedsAttentionEntry]


def status_counts(articles: list[Article]) -> dict[Status, int]:
    counts = dict.fromkeys(Status, 0)
    for article in articles:
        counts[article.status] += 1
    return counts


def published_this_month(
    articles: list[Article], events_by_article: EventsByArticle, now: datetime
) -> int:
    count = 0
    for article in articles:
        events = events_by_article.get(article.id, [])
        if any(
            e.type == EventType.PUBLISHED and e.at.year == now.year and e.at.month == now.month
            for e in events
        ):
            count += 1
    return count


def avg_approval_seconds(
    articles: list[Article], events_by_article: EventsByArticle
) -> float | None:
    durations: list[float] = []
    for article in articles:
        events = events_by_article.get(article.id, [])
        first_sent = next((e for e in events if e.type == EventType.SENT_FOR_REVIEW), None)
        approved = next((e for e in events if e.type == EventType.APPROVED), None)
        if first_sent is not None and approved is not None:
            durations.append((approved.at - first_sent.at).total_seconds())
    if not durations:
        return None
    return sum(durations) / len(durations)


def change_rounds(
    articles: list[Article], events_by_article: EventsByArticle
) -> list[ChangeRoundsEntry]:
    entries = []
    for article in articles:
        events = events_by_article.get(article.id, [])
        rounds = sum(1 for e in events if e.type == EventType.CHANGES_REQUESTED)
        if rounds > 0:
            entries.append(ChangeRoundsEntry(article.id, article.title, rounds))
    return entries


def avg_change_rounds(articles: list[Article], rounds: list[ChangeRoundsEntry]) -> float | None:
    """Change requests per article, over every article; None with no articles."""
    if not articles:
        return None
    return sum(r.rounds for r in rounds) / len(articles)


def upcoming(articles: list[Article]) -> list[UpcomingEntry]:
    entries = [
        UpcomingEntry(a.id, a.title, a.publish_at_utc)
        for a in articles
        if a.status == Status.SCHEDULED and a.publish_at_utc is not None
    ]
    entries.sort(key=lambda e: e.publish_at_utc)
    return entries


def published(articles: list[Article], events_by_article: EventsByArticle) -> list[PublishedEntry]:
    entries = []
    for article in articles:
        if article.status != Status.PUBLISHED or article.published_url is None:
            continue
        events = events_by_article.get(article.id, [])
        published_events = [e for e in events if e.type == EventType.PUBLISHED]
        published_at = max((e.at for e in published_events), default=article.updated_at)
        entries.append(
            PublishedEntry(article.id, article.title, article.published_url, published_at)
        )
    entries.sort(key=lambda e: e.published_at, reverse=True)
    return entries


def needs_attention(articles: list[Article]) -> list[NeedsAttentionEntry]:
    entries = []
    for article in articles:
        if article.status == Status.FAILED:
            entries.append(
                NeedsAttentionEntry(article.id, article.title, "failed", article.last_error)
            )
        elif article.sync_warning is not None:
            entries.append(
                NeedsAttentionEntry(article.id, article.title, article.sync_warning.value, None)
            )
    return entries
