from datetime import UTC, datetime

import pytest

from app.adapters.testing.in_memory_repository import InMemoryArticleRepository
from app.core.domain.errors import ArticleNotVisibleError, InvalidTokenError
from app.core.domain.models import Article, Site
from app.core.domain.statuses import Status
from app.core.lib.tokens import hash_token
from app.core.use_cases.review import get_review_article, get_review_page

NOW = datetime(2026, 10, 7, 12, 0, 0, tzinfo=UTC)
TOKEN = "the-real-token"


def _article(article_id: str, status: Status) -> Article:
    return Article(
        id=article_id,
        title=f"Article {article_id}",
        slug=article_id,
        body_html="<p>body</p>",
        source="paste",
        status=status,
        version=1,
        created_at=NOW,
        updated_at=NOW,
    )


@pytest.fixture
def repository():
    repo = InMemoryArticleRepository()
    repo.save_site(
        Site(
            id="s1",
            name="Test site",
            wp_base_url="https://wp.example.com",
            review_token_hash=hash_token(TOKEN),
        )
    )
    return repo


def test_groups_articles_into_visible_buckets_only(repository):
    for status in Status:
        repository.create_article(_article(status.value, status))

    site, groups = get_review_page(repository, TOKEN)

    assert site.name == "Test site"
    assert [a.id for a in groups[Status.AWAITING_APPROVAL]] == ["awaiting_approval"]
    assert [a.id for a in groups[Status.SCHEDULED]] == ["scheduled"]
    assert [a.id for a in groups[Status.PUBLISHED]] == ["published"]
    visible_ids = {a.id for articles in groups.values() for a in articles}
    assert visible_ids == {"awaiting_approval", "scheduled", "published"}


def test_wrong_token_raises(repository):
    repository.create_article(_article("a1", Status.PUBLISHED))
    with pytest.raises(InvalidTokenError):
        get_review_page(repository, "not-the-token")


def test_no_token_set_on_site_raises():
    repo = InMemoryArticleRepository()
    repo.save_site(Site(id="s1", name="Test site", wp_base_url="https://wp.example.com"))
    with pytest.raises(InvalidTokenError):
        get_review_page(repo, TOKEN)


@pytest.mark.parametrize("status", [Status.AWAITING_APPROVAL, Status.SCHEDULED, Status.PUBLISHED])
def test_get_review_article_returns_visible_article(repository, status):
    repository.create_article(_article("a1", status))
    article = get_review_article(repository, TOKEN, "a1")
    assert article.id == "a1"


@pytest.mark.parametrize("status", [Status.DRAFT, Status.CHANGES_REQUESTED, Status.FAILED])
def test_get_review_article_hides_non_visible_statuses(repository, status):
    repository.create_article(_article("a1", status))
    with pytest.raises(ArticleNotVisibleError):
        get_review_article(repository, TOKEN, "a1")


def test_get_review_article_unknown_id_raises(repository):
    with pytest.raises(ArticleNotVisibleError):
        get_review_article(repository, TOKEN, "missing")


def test_get_review_article_wrong_token_raises(repository):
    repository.create_article(_article("a1", Status.PUBLISHED))
    with pytest.raises(InvalidTokenError):
        get_review_article(repository, "not-the-token", "a1")
