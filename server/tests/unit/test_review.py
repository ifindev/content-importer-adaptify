from datetime import UTC, datetime

import pytest

from app.adapters.testing.clock import FixedClock
from app.adapters.testing.in_memory_repository import InMemoryArticleRepository
from app.core.domain.errors import NotAwaitingApprovalError, NotSendableError
from app.core.domain.models import Article
from app.core.domain.statuses import Status
from app.core.use_cases.review import pull_back, send_for_review

NOW = datetime(2026, 10, 7, 12, 0, 0, tzinfo=UTC)

SENDABLE = [Status.DRAFT, Status.CHANGES_REQUESTED]
NOT_SENDABLE = [
    Status.AWAITING_APPROVAL,
    Status.APPROVED,
    Status.SCHEDULED,
    Status.PUBLISHED,
    Status.FAILED,
]
NOT_AWAITING_APPROVAL = [
    Status.DRAFT,
    Status.CHANGES_REQUESTED,
    Status.APPROVED,
    Status.SCHEDULED,
    Status.PUBLISHED,
    Status.FAILED,
]


def _article(status: Status) -> Article:
    return Article(
        id="a1",
        title="Title",
        slug="title",
        body_html="<p>hi</p>",
        source="paste",
        status=status,
        version=1,
        created_at=NOW,
        updated_at=NOW,
    )


@pytest.fixture
def repository():
    return InMemoryArticleRepository()


@pytest.fixture
def clock():
    return FixedClock(NOW)


@pytest.mark.parametrize("status", SENDABLE)
def test_send_for_review_allowed_statuses(status, repository, clock):
    article = _article(status)
    repository.create_article(article)

    updated = send_for_review(article, repository, clock, "agency")

    assert updated.status == Status.AWAITING_APPROVAL
    events = repository.list_events("a1")
    assert events[-1].type.value == "sent_for_review"
    assert events[-1].actor == "agency"
    assert events[-1].at == NOW


@pytest.mark.parametrize("status", NOT_SENDABLE)
def test_send_for_review_refused_from_other_statuses(status, repository, clock):
    article = _article(status)
    repository.create_article(article)

    with pytest.raises(NotSendableError):
        send_for_review(article, repository, clock, "agency")


def test_pull_back_from_awaiting_approval(repository, clock):
    article = _article(Status.AWAITING_APPROVAL)
    repository.create_article(article)

    updated = pull_back(article, repository, clock, "agency")

    assert updated.status == Status.DRAFT
    events = repository.list_events("a1")
    assert events[-1].type.value == "pulled_back"
    assert events[-1].actor == "agency"


@pytest.mark.parametrize("status", NOT_AWAITING_APPROVAL)
def test_pull_back_refused_from_other_statuses(status, repository, clock):
    article = _article(status)
    repository.create_article(article)

    with pytest.raises(NotAwaitingApprovalError):
        pull_back(article, repository, clock, "agency")
