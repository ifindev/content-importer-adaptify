from pathlib import Path
from zipfile import BadZipFile

import pytest

from app.adapters.documents.parser import RealDocumentParser

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture
def parser() -> RealDocumentParser:
    return RealDocumentParser()


def test_clean_html_strips_disallowed_tags_and_attrs(parser):
    html = '<h2 style="color:red">Title</h2><p class="x">Body <script>evil()</script></p>'
    parsed = parser.clean_html(html)
    assert parsed.title == "Title"
    assert "script" not in parsed.body_html
    assert "style" not in parsed.body_html
    assert "class" not in parsed.body_html
    assert "<p>Body" in parsed.body_html


def test_clean_html_keeps_allowed_structure(parser):
    html = (
        "<h2>T</h2><p><strong>b</strong> <em>i</em> "
        '<a href="https://x.com">link</a></p>'
        "<ul><li>one</li></ul><ol><li>two</li></ol>"
        "<table><tr><td>a</td></tr></table>"
    )
    parsed = parser.clean_html(html)
    for tag in ("strong", "em", "a href", "ul", "li", "ol", "table", "td"):
        assert tag.split()[0] in parsed.body_html


def test_clean_html_drops_images(parser):
    parsed = parser.clean_html("<h2>T</h2><p>body</p><img src='x.png'>")
    assert "img" not in parsed.body_html


def test_clean_html_no_heading_means_no_title(parser):
    parsed = parser.clean_html("<p>just a paragraph</p>")
    assert parsed.title is None


def test_clean_html_promotes_uniform_headings(parser):
    parsed = parser.clean_html("<h1>Title</h1><h3>A</h3><p>x</p><h3>B</h3><p>y</p>")
    assert parsed.title == "Title"
    assert parsed.body_html.count("<h2>") == 2
    assert "<h3>" not in parsed.body_html


def test_clean_html_mixed_levels_not_promoted(parser):
    parsed = parser.clean_html("<h1>Title</h1><h2>A</h2><p>x</p><h3>B</h3><p>y</p>")
    assert "<h2>A</h2>" in parsed.body_html
    assert "<h3>B</h3>" in parsed.body_html


def test_parse_docx_with_image_warns_and_drops_image(parser):
    content = (FIXTURES / "with_image.docx").read_bytes()
    parsed = parser.parse_docx(content, "with_image.docx")
    assert parsed.warnings == ["This document had 1 images. Images are not imported."]
    assert "img" not in parsed.body_html


def test_parse_docx_with_table_keeps_table(parser):
    content = (FIXTURES / "with_table.docx").read_bytes()
    parsed = parser.parse_docx(content, "with_table.docx")
    assert "<table>" in parsed.body_html
    assert "A1" in parsed.body_html


def test_parse_docx_title_from_first_heading(parser):
    content = (FIXTURES / "heading_simple.docx").read_bytes()
    parsed = parser.parse_docx(content, "heading_simple.docx")
    assert parsed.title == "Fixture Title"
    assert "Fixture Title" not in parsed.body_html


def test_parse_docx_corrupt_file_raises(parser):
    content = (FIXTURES / "corrupt.docx").read_bytes()
    with pytest.raises(BadZipFile):
        parser.parse_docx(content, "corrupt.docx")


def test_parse_docx_realistic_article_end_to_end(parser):
    """A genuine multi-section article, not a narrow single-concern fixture:
    exercises title extraction, uniform-heading sections, bold/italic, a list that
    isn't in the allowed set, lists, and a table all together, like a real import.
    """
    content = (FIXTURES / "realistic_article.docx").read_bytes()
    parsed = parser.parse_docx(content, "realistic_article.docx")

    assert parsed.title == "How Remote Work Is Reshaping Modern Teams"
    assert parsed.warnings == []
    assert parsed.title not in parsed.body_html

    # Section headings kept, at the uniform level they already were.
    assert parsed.body_html.count("<h2>") == 4
    for heading in ("Flexibility Gains", "Communication Challenges", "Looking Ahead"):
        assert f"<h2>{heading}</h2>" in parsed.body_html

    # Formatting kept where allowed, stripped where not (underline isn't in nh3's
    # allowed tags, but its text survives).
    assert "<strong>deliberate</strong>" in parsed.body_html
    assert "<em>hallway conversations</em>" in parsed.body_html
    assert "see this guide for details" in parsed.body_html
    assert "<u>" not in parsed.body_html

    # Both list types and the table survive structurally.
    assert "<ul>" in parsed.body_html and "<li>Fewer commutes</li>" in parsed.body_html
    assert "<ol>" in parsed.body_html and "Write decisions down" in parsed.body_html
    assert "<table>" in parsed.body_html
    assert "<td><p>62%</p></td>" in parsed.body_html
