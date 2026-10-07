from datetime import UTC, datetime

import pytest

from app.adapters.testing.clock import FixedClock
from app.adapters.testing.in_memory_repository import InMemoryArticleRepository
from app.core.domain.errors import (
    ArticleChangedError,
    ArticleNotVisibleError,
    InvalidTokenError,
    NotAwaitingApprovalError,
)
from app.core.domain.models import Article
from app.core.domain.statuses import Status
from app.core.lib.tokens import hash_token
from app.core.use_cases.review import approve, request_changes

NOW = datetime(2026, 10, 7, 12, 0, 0, tzinfo=UTC)
TOKEN = "the-real-token"

NOT_AWAITING_APPROVAL = [
    Status.DRAFT,
    Status.CHANGES_REQUESTED,
    Status.APPROVED,
    Status.SCHEDULED,
    Status.PUBLISHED,
    Status.FAILED,
]


def _article(status: Status, version: int = 1, client_comment: str | None = None) -> Article:
    return Article(
        id="a1",
        title="Title",
        slug="title",
        body_html="<p>hi</p>",
        source="paste",
        status=status,
        version=version,
        client_comment=client_comment,
        created_at=NOW,
        updated_at=NOW,
    )


@pytest.fixture
def repository():
    repo = InMemoryArticleRepository()
    repo.ensure_site_bootstrapped("Test site", "https://wp.example.com")
    repo.save_site(repo.get_site().model_copy(update={"review_token_hash": hash_token(TOKEN)}))
    return repo


@pytest.fixture
def clock():
    return FixedClock(NOW)


def test_approve_moves_awaiting_approval_to_approved(repository, clock):
    article = _article(Status.AWAITING_APPROVAL, version=3, client_comment="old feedback")
    repository.create_article(article)

    updated = approve(repository, clock, TOKEN, "a1", "Jane Client", 3)

    assert updated.status == Status.APPROVED
    assert updated.approved_version == 3
    assert updated.client_comment is None
    events = repository.list_events("a1")
    assert events[-1].type.value == "approved"
    assert events[-1].actor == "Jane Client"
    assert events[-1].at == NOW


@pytest.mark.parametrize("status", NOT_AWAITING_APPROVAL)
def test_approve_refused_from_other_statuses(status, repository, clock):
    article = _article(status, version=3)
    repository.create_article(article)

    with pytest.raises(NotAwaitingApprovalError):
        approve(repository, clock, TOKEN, "a1", "Jane Client", 3)


def test_approve_refuses_stale_version(repository, clock):
    article = _article(Status.AWAITING_APPROVAL, version=3)
    repository.create_article(article)

    with pytest.raises(ArticleChangedError):
        approve(repository, clock, TOKEN, "a1", "Jane Client", 2)


def test_approve_status_check_takes_precedence_over_version(repository, clock):
    article = _article(Status.DRAFT, version=3)
    repository.create_article(article)

    with pytest.raises(NotAwaitingApprovalError):
        approve(repository, clock, TOKEN, "a1", "Jane Client", 3)


def test_approve_unknown_article_raises(repository, clock):
    with pytest.raises(ArticleNotVisibleError):
        approve(repository, clock, TOKEN, "missing", "Jane Client", 1)


def test_approve_wrong_token_raises(repository, clock):
    article = _article(Status.AWAITING_APPROVAL, version=1)
    repository.create_article(article)

    with pytest.raises(InvalidTokenError):
        approve(repository, clock, "not-the-token", "a1", "Jane Client", 1)


def test_request_changes_moves_awaiting_approval_to_changes_requested(repository, clock):
    article = _article(Status.AWAITING_APPROVAL, version=3)
    repository.create_article(article)

    updated = request_changes(
        repository, clock, TOKEN, "a1", "Jane Client", "please fix the intro", 3
    )

    assert updated.status == Status.CHANGES_REQUESTED
    assert updated.client_comment == "please fix the intro"
    events = repository.list_events("a1")
    assert events[-1].type.value == "changes_requested"
    assert events[-1].actor == "Jane Client"
    assert events[-1].data == {"comment": "please fix the intro"}


@pytest.mark.parametrize("status", NOT_AWAITING_APPROVAL)
def test_request_changes_refused_from_other_statuses(status, repository, clock):
    article = _article(status, version=3)
    repository.create_article(article)

    with pytest.raises(NotAwaitingApprovalError):
        request_changes(repository, clock, TOKEN, "a1", "Jane Client", "comment", 3)


def test_request_changes_refuses_stale_version(repository, clock):
    article = _article(Status.AWAITING_APPROVAL, version=3)
    repository.create_article(article)

    with pytest.raises(ArticleChangedError):
        request_changes(repository, clock, TOKEN, "a1", "Jane Client", "comment", 2)


def test_request_changes_unknown_article_raises(repository, clock):
    with pytest.raises(ArticleNotVisibleError):
        request_changes(repository, clock, TOKEN, "missing", "Jane Client", "comment", 1)
