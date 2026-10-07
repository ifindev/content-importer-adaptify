from datetime import UTC, datetime

import pytest

from app.adapters.testing.clock import FixedClock
from app.adapters.testing.in_memory_repository import InMemoryArticleRepository
from app.core.domain.errors import EmptyContentError
from app.core.ports.document_parser import ParsedDocument
from app.core.use_cases.import_article import import_from_docx, import_from_paste

NOW = datetime(2026, 10, 7, 12, 0, 0, tzinfo=UTC)


class FakeParser:
    def __init__(self, clean=None, docx=None) -> None:
        self._clean = clean or ParsedDocument(title="Title", body_html="<p>body</p>")
        self._docx = docx or ParsedDocument(title="Title", body_html="<p>body</p>")

    def clean_html(self, html: str) -> ParsedDocument:
        return self._clean

    def parse_docx(self, content: bytes, filename: str) -> ParsedDocument:
        return self._docx


@pytest.fixture
def repository():
    return InMemoryArticleRepository()


@pytest.fixture
def clock():
    return FixedClock(NOW)


def test_import_from_paste_creates_draft_article(repository, clock):
    parser = FakeParser(clean=ParsedDocument(title="Title", body_html="<p>body</p>"))
    article = import_from_paste("<h1>Title</h1><p>body</p>", repository, parser, clock, "uid1")

    assert article.source == "paste"
    assert article.source_filename is None
    assert article.status.value == "draft"
    assert article.title == "Title"
    events = repository.list_events(article.id)
    assert [e.type.value for e in events] == ["imported"]
    assert events[0].actor == "uid1"


def test_import_from_paste_defaults_title_to_untitled(repository, clock):
    parser = FakeParser(clean=ParsedDocument(title=None, body_html="<p>body</p>"))
    article = import_from_paste("<p>body</p>", repository, parser, clock, "uid1")
    assert article.title == "Untitled"


def test_import_from_paste_empty_after_cleaning_raises(repository, clock):
    parser = FakeParser(clean=ParsedDocument(title="T", body_html="   "))
    with pytest.raises(EmptyContentError):
        import_from_paste("<p></p>", repository, parser, clock, "uid1")


def test_import_from_docx_sets_source_and_filename(repository, clock):
    parser = FakeParser(docx=ParsedDocument(title="Doc Title", body_html="<p>body</p>"))
    article = import_from_docx("report.docx", b"bytes", repository, parser, clock, "uid1")

    assert article.source == "docx"
    assert article.source_filename == "report.docx"
    assert article.title == "Doc Title"


def test_import_from_docx_title_falls_back_to_filename(repository, clock):
    parser = FakeParser(docx=ParsedDocument(title=None, body_html="<p>body</p>"))
    article = import_from_docx("my-report.docx", b"bytes", repository, parser, clock, "uid1")
    assert article.title == "my-report"
