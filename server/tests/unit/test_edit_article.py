from datetime import UTC, datetime

import pytest

from app.adapters.testing.clock import FixedClock
from app.adapters.testing.in_memory_repository import InMemoryArticleRepository
from app.core.domain.errors import NotEditableError
from app.core.domain.models import Article
from app.core.domain.statuses import Status
from app.core.ports.document_parser import ParsedDocument
from app.core.use_cases.edit_article import edit_article

CREATED = datetime(2026, 10, 1, 9, 0, 0, tzinfo=UTC)
NOW = datetime(2026, 10, 7, 12, 0, 0, tzinfo=UTC)

EDITABLE = [Status.DRAFT, Status.CHANGES_REQUESTED, Status.APPROVED, Status.SCHEDULED]
NOT_EDITABLE = [Status.AWAITING_APPROVAL, Status.PUBLISHED, Status.FAILED]
RESET_FROM = {Status.APPROVED: "approved", Status.SCHEDULED: "scheduled"}


class FakeParser:
    def clean_html(self, html: str) -> ParsedDocument:
        return ParsedDocument(title=None, body_html=f"cleaned:{html}")


def _article(status: Status, approved_version: int | None = 2) -> Article:
    return Article(
        id="a1",
        title="Old Title",
        slug="old-title",
        body_html="<p>old</p>",
        source="paste",
        status=status,
        version=3,
        approved_version=approved_version,
        created_at=CREATED,
        updated_at=CREATED,
    )


@pytest.fixture
def repository():
    repo = InMemoryArticleRepository()
    return repo


@pytest.fixture
def clock():
    return FixedClock(NOW)


@pytest.mark.parametrize("status", EDITABLE)
def test_edit_allowed_statuses_bump_version(status, repository, clock):
    article = _article(status)
    repository.create_article(article)

    updated = edit_article(
        article, "New Title", None, None, repository, FakeParser(), clock, "uid"
    )

    assert updated.version == 4
    assert updated.title == "New Title"
    assert updated.slug == "old-title"
    assert updated.approved_version == 2


@pytest.mark.parametrize("status", [Status.APPROVED, Status.SCHEDULED])
def test_edit_resets_approved_and_scheduled_to_draft(status, repository, clock):
    article = _article(status)
    repository.create_article(article)

    updated = edit_article(article, None, None, None, repository, FakeParser(), clock, "uid")

    assert updated.status == Status.DRAFT
    events = repository.list_events("a1")
    assert events[-1].type.value == "edited"
    assert events[-1].data == {"reset_from": RESET_FROM[status]}


@pytest.mark.parametrize("status", [Status.DRAFT, Status.CHANGES_REQUESTED])
def test_edit_does_not_reset_draft_or_changes_requested(status, repository, clock):
    article = _article(status)
    repository.create_article(article)

    updated = edit_article(article, None, None, None, repository, FakeParser(), clock, "uid")

    assert updated.status == status
    events = repository.list_events("a1")
    assert events[-1].data is None


@pytest.mark.parametrize("status", NOT_EDITABLE)
def test_edit_refused_from_non_editable_statuses(status, repository, clock):
    article = _article(status)
    repository.create_article(article)

    with pytest.raises(NotEditableError):
        edit_article(article, "x", None, None, repository, FakeParser(), clock, "uid")


def test_edit_no_op_still_bumps_version_and_appends_event(repository, clock):
    article = _article(Status.DRAFT)
    repository.create_article(article)

    updated = edit_article(
        article,
        article.title,
        article.slug,
        article.body_html,
        repository,
        FakeParser(),
        clock,
        "uid",
    )

    assert updated.version == 4
    assert len(repository.list_events("a1")) == 1


def test_edit_body_html_is_recleaned(repository, clock):
    article = _article(Status.DRAFT)
    repository.create_article(article)

    updated = edit_article(
        article, None, None, "<script>evil()</script>", repository, FakeParser(), clock, "uid"
    )

    assert updated.body_html == "cleaned:<script>evil()</script>"


def test_edit_partial_update_leaves_other_fields(repository, clock):
    article = _article(Status.DRAFT)
    repository.create_article(article)

    updated = edit_article(article, None, "new-slug", None, repository, FakeParser(), clock, "uid")

    assert updated.slug == "new-slug"
    assert updated.title == "Old Title"
    assert updated.body_html == "<p>old</p>"
