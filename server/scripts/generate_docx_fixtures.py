"""One-off generator for server/tests/fixtures/*.docx.

Run with `uv run python scripts/generate_docx_fixtures.py`.
"""

from pathlib import Path

import docx

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "tests" / "fixtures"


def heading_simple() -> None:
    doc = docx.Document()
    doc.add_heading("Fixture Title", level=1)
    doc.add_paragraph("First paragraph of body text.")
    doc.add_paragraph("Second paragraph of body text.")
    doc.save(FIXTURES_DIR / "heading_simple.docx")


def heading_and_lists() -> None:
    doc = docx.Document()
    doc.add_heading("Lists And Links", level=1)
    p = doc.add_paragraph()
    p.add_run("Some ").bold = False
    p.add_run("bold").bold = True
    p.add_run(" and ")
    p.add_run("italic").italic = True
    p.add_run(" text, plus a link: ")
    p.add_run("example.com")
    doc.add_paragraph("Bullet one", style="List Bullet")
    doc.add_paragraph("Bullet two", style="List Bullet")
    doc.add_paragraph("Number one", style="List Number")
    doc.add_paragraph("Number two", style="List Number")
    doc.save(FIXTURES_DIR / "heading_and_lists.docx")


# A valid, minimal 1x1 pixel PNG, so the fixture needs no imaging dependency.
_TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00"
    b"\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x03\x01\x01\x00\x18\xdd\x8d\xb0"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


def with_image() -> None:
    import io

    doc = docx.Document()
    doc.add_heading("Document With Image", level=1)
    doc.add_picture(io.BytesIO(_TINY_PNG))
    doc.add_paragraph("Paragraph after the image.")
    doc.save(FIXTURES_DIR / "with_image.docx")


def with_table() -> None:
    doc = docx.Document()
    doc.add_heading("Document With Table", level=1)
    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "A1"
    table.cell(0, 1).text = "B1"
    table.cell(1, 0).text = "A2"
    table.cell(1, 1).text = "B2"
    doc.save(FIXTURES_DIR / "with_table.docx")


def mixed_heading_levels() -> None:
    doc = docx.Document()
    doc.add_heading("Mixed Heading Levels", level=1)
    doc.add_heading("Section A", level=2)
    doc.add_paragraph("Body under section A.")
    doc.add_heading("Subsection", level=3)
    doc.add_paragraph("Body under subsection.")
    doc.save(FIXTURES_DIR / "mixed_heading_levels.docx")


def uniform_headings() -> None:
    # Level 3 throughout, so the fixture actually exercises R1.6's promotion
    # (section headings rewritten to h2), not a no-op where they're already h2.
    doc = docx.Document()
    doc.add_heading("Uniform Headings", level=1)
    doc.add_heading("Section One", level=3)
    doc.add_paragraph("Body one.")
    doc.add_heading("Section Two", level=3)
    doc.add_paragraph("Body two.")
    doc.add_heading("Section Three", level=3)
    doc.add_paragraph("Body three.")
    doc.save(FIXTURES_DIR / "uniform_headings.docx")


def realistic_article() -> None:
    # A genuine multi-section article (not a narrow single-concern fixture like the
    # others above), so the full import pipeline gets exercised on something that
    # actually looks like what an agency would paste or upload: a real title, several
    # uniform-level sections, bold/italic, a link, a bulleted and a numbered list, and
    # a table, all in one document.
    doc = docx.Document()
    doc.add_heading("How Remote Work Is Reshaping Modern Teams", level=1)
    doc.add_paragraph(
        "Remote work has moved from a pandemic-era stopgap to a permanent fixture of "
        "how modern teams operate. Companies that adapted early are now reaping the "
        "benefits, while those that resisted are rethinking their approach."
    )

    doc.add_heading("Flexibility Gains", level=2)
    doc.add_paragraph(
        "The single biggest advantage employees report is control over their own schedule."
    )
    doc.add_paragraph("Fewer commutes", style="List Bullet")
    doc.add_paragraph("More overlap with personal errands", style="List Bullet")
    doc.add_paragraph("Easier focus blocks for deep work", style="List Bullet")

    doc.add_heading("Communication Challenges", level=2)
    p = doc.add_paragraph("Distributed teams must be ")
    p.add_run("deliberate").bold = True
    p.add_run(" about how they communicate, since ")
    p.add_run("hallway conversations").italic = True
    p.add_run(" simply don't happen anymore. Many teams now follow a written-first policy; ")
    p.add_run("see this guide for details").underline = True
    p.add_run(".")
    doc.add_paragraph("Write decisions down, don't just discuss them", style="List Number")
    doc.add_paragraph("Default to async, escalate to sync only when stuck", style="List Number")
    doc.add_paragraph("Over-communicate context for new teammates", style="List Number")

    doc.add_heading("Adoption By Company Size", level=2)
    table = doc.add_table(rows=3, cols=2)
    table.cell(0, 0).text = "Company size"
    table.cell(0, 1).text = "Fully remote"
    table.cell(1, 0).text = "Under 50"
    table.cell(1, 1).text = "62%"
    table.cell(2, 0).text = "50-500"
    table.cell(2, 1).text = "41%"

    doc.add_heading("Looking Ahead", level=2)
    doc.add_paragraph(
        "The teams that win the next decade won't be the ones that mandate a return "
        "to the office, but the ones that build real systems for working apart well."
    )
    doc.save(FIXTURES_DIR / "realistic_article.docx")


def corrupt() -> None:
    (FIXTURES_DIR / "corrupt.docx").write_bytes(b"not a real docx file")


def main() -> None:
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    heading_simple()
    heading_and_lists()
    with_image()
    with_table()
    mixed_heading_levels()
    uniform_headings()
    realistic_article()
    corrupt()


if __name__ == "__main__":
    main()
