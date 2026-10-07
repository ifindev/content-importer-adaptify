from datetime import UTC, datetime

from app.core.domain.models import Article, Event
from app.core.domain.report import (
    avg_approval_seconds,
    change_rounds,
    needs_attention,
    published,
    published_this_month,
    status_counts,
    upcoming,
)
from app.core.domain.statuses import EventType, Status, SyncWarning

NOW = datetime(2026, 10, 7, 12, 0, 0, tzinfo=UTC)


def _article(id_: str, status: Status = Status.DRAFT, **overrides) -> Article:
    return Article(
        id=id_,
        title=f"Title {id_}",
        slug=id_,
        body_html="<p>hi</p>",
        source="paste",
        status=status,
        version=1,
        created_at=NOW,
        updated_at=NOW,
        **overrides,
    )


def _event(type_: EventType, at: datetime) -> Event:
    return Event(id=f"e-{type_}-{at.isoformat()}", type=type_, actor="test", at=at)


def test_status_counts_all_zero_when_no_articles():
    counts = status_counts([])
    assert counts == {s: 0 for s in Status}


def test_status_counts_across_all_statuses():
    articles = [_article(s.value, status=s) for s in Status]
    counts = status_counts(articles)
    assert counts == {s: 1 for s in Status}


def test_published_this_month_counts_only_current_utc_month():
    in_month = _article("a1", status=Status.PUBLISHED)
    out_of_month = _article("a2", status=Status.PUBLISHED)
    events = {
        "a1": [_event(EventType.PUBLISHED, datetime(2026, 10, 1, tzinfo=UTC))],
        "a2": [_event(EventType.PUBLISHED, datetime(2026, 9, 30, tzinfo=UTC))],
    }
    assert published_this_month([in_month, out_of_month], events, NOW) == 1


def test_avg_approval_seconds_none_when_nobody_approved():
    article = _article("a1")
    events = {"a1": [_event(EventType.SENT_FOR_REVIEW, NOW)]}
    assert avg_approval_seconds([article], events) is None


def test_avg_approval_seconds_uses_first_sent_for_review():
    article = _article("a1", status=Status.APPROVED)
    first_sent = datetime(2026, 10, 1, tzinfo=UTC)
    pulled_back_and_resent = datetime(2026, 10, 2, tzinfo=UTC)
    approved_at = datetime(2026, 10, 3, tzinfo=UTC)
    events = {
        "a1": [
            _event(EventType.SENT_FOR_REVIEW, first_sent),
            _event(EventType.PULLED_BACK, datetime(2026, 10, 1, 12, tzinfo=UTC)),
            _event(EventType.SENT_FOR_REVIEW, pulled_back_and_resent),
            _event(EventType.APPROVED, approved_at),
        ]
    }
    expected = (approved_at - first_sent).total_seconds()
    assert avg_approval_seconds([article], events) == expected


def test_change_rounds_only_includes_articles_with_at_least_one_round():
    with_changes = _article("a1")
    without_changes = _article("a2")
    events = {
        "a1": [
            _event(EventType.CHANGES_REQUESTED, NOW),
            _event(EventType.CHANGES_REQUESTED, NOW),
        ],
        "a2": [],
    }
    entries = change_rounds([with_changes, without_changes], events)
    assert len(entries) == 1
    assert entries[0].article_id == "a1"
    assert entries[0].rounds == 2


def test_upcoming_sorted_soonest_first():
    later = _article(
        "a1", status=Status.SCHEDULED, publish_at_utc=datetime(2026, 11, 1, tzinfo=UTC)
    )
    sooner = _article(
        "a2", status=Status.SCHEDULED, publish_at_utc=datetime(2026, 10, 10, tzinfo=UTC)
    )
    entries = upcoming([later, sooner])
    assert [e.article_id for e in entries] == ["a2", "a1"]


def test_published_sorted_most_recent_first():
    older = _article("a1", status=Status.PUBLISHED, published_url="https://x/a1")
    newer = _article("a2", status=Status.PUBLISHED, published_url="https://x/a2")
    events = {
        "a1": [_event(EventType.PUBLISHED, datetime(2026, 9, 1, tzinfo=UTC))],
        "a2": [_event(EventType.PUBLISHED, datetime(2026, 10, 1, tzinfo=UTC))],
    }
    entries = published([older, newer], events)
    assert [e.article_id for e in entries] == ["a2", "a1"]


def test_needs_attention_lists_failed_and_sync_warnings():
    failed = _article("a1", status=Status.FAILED, last_error="WordPress 500")
    late = _article("a2", sync_warning=SyncWarning.LATE)
    fine = _article("a3")
    entries = needs_attention([failed, late, fine])
    by_id = {e.article_id: e for e in entries}
    assert set(by_id) == {"a1", "a2"}
    assert by_id["a1"].reason == "failed"
    assert by_id["a1"].detail == "WordPress 500"
    assert by_id["a2"].reason == "late"
    assert by_id["a2"].detail is None
