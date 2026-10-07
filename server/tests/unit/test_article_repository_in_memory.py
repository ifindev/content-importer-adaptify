from datetime import UTC, datetime

from app.adapters.testing.in_memory_repository import InMemoryArticleRepository
from app.core.domain.models import Article, Event, Site
from app.core.domain.statuses import EventType, Status

NOW = datetime(2026, 10, 7, 12, 0, 0, tzinfo=UTC)


def _article(id_: str, status: Status = Status.DRAFT) -> Article:
    return Article(
        id=id_,
        title="Title",
        slug="title",
        body_html="<p>hi</p>",
        source="paste",
        status=status,
        version=1,
        created_at=NOW,
        updated_at=NOW,
    )


def test_save_site_then_get_site_round_trips():
    repo = InMemoryArticleRepository()
    site = Site(id="s1", name="My Site", wp_base_url="https://wp.example")
    repo.save_site(site)
    assert repo.get_site() == site


def test_create_and_get_article():
    repo = InMemoryArticleRepository()
    repo.create_article(_article("a1"))
    assert repo.get_article("a1").id == "a1"
    assert repo.get_article("missing") is None


def test_list_articles_filters_by_status():
    repo = InMemoryArticleRepository()
    repo.create_article(_article("a1", Status.DRAFT))
    repo.create_article(_article("a2", Status.APPROVED))

    assert {a.id for a in repo.list_articles()} == {"a1", "a2"}
    assert [a.id for a in repo.list_articles(status=Status.APPROVED)] == ["a2"]


def test_save_article_appends_event():
    repo = InMemoryArticleRepository()
    article = repo.create_article(_article("a1"))
    updated = article.model_copy(update={"status": Status.AWAITING_APPROVAL})
    event = Event(id="e1", type=EventType.SENT_FOR_REVIEW, actor="agency", at=NOW)

    repo.save_article(updated, event)

    assert repo.get_article("a1").status == Status.AWAITING_APPROVAL
    assert [e.id for e in repo.list_events("a1")] == ["e1"]
