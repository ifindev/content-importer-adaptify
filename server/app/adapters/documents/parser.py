import re
from io import BytesIO

import mammoth
import nh3

from app.core.lib.html_rules import ALLOWED_ATTRIBUTES, ALLOWED_TAGS
from app.core.ports.document_parser import ParsedDocument

# ponytail: regex over full HTML tags, mammoth/pasted output is flat, non-nested heading
# markup; revisit with a real HTML parser (html.parser/lxml) if nested markup ever appears.
_HEADING_RE = re.compile(r"<h([1-6])[^>]*>(.*?)</h\1>", re.IGNORECASE | re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")
_IMG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)


def _image_warnings(count: int) -> list[str]:
    if not count:
        return []
    images = "1 image" if count == 1 else f"{count} images"
    return [f"This document had {images}. Images are not imported."]


def _strip_tags(html: str) -> str:
    return _TAG_RE.sub("", html).strip()


def _extract_title(html: str) -> tuple[str | None, str]:
    match = _HEADING_RE.search(html)
    if match is None:
        return None, html
    title = _strip_tags(match.group(2))
    body = html[: match.start()] + html[match.end() :]
    return title or None, body


def _promote_uniform_headings(html: str) -> str:
    levels = {int(level) for level, _ in _HEADING_RE.findall(html)}
    if len(levels) != 1:
        return html
    (level,) = levels
    if level == 2:
        return html
    html = re.sub(rf"<h{level}(\s[^>]*)?>", "<h2>", html, flags=re.IGNORECASE)
    return re.sub(rf"</h{level}>", "</h2>", html, flags=re.IGNORECASE)


def _clean(html: str) -> tuple[str | None, str]:
    title, body = _extract_title(html)
    body = _promote_uniform_headings(body)
    cleaned = nh3.clean(body, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)
    return title, cleaned.strip()


class RealDocumentParser:
    def clean_html(self, html: str) -> ParsedDocument:
        warnings = _image_warnings(len(_IMG_RE.findall(html)))
        title, body = _clean(html)
        return ParsedDocument(title=title, body_html=body, warnings=warnings)

    def parse_docx(self, content: bytes, filename: str) -> ParsedDocument:
        image_count = 0

        def _handle_image(image):
            nonlocal image_count
            image_count += 1
            return {}

        result = mammoth.convert_to_html(
            BytesIO(content), convert_image=mammoth.images.img_element(_handle_image)
        )
        title, body = _clean(result.value)
        return ParsedDocument(title=title, body_html=body, warnings=_image_warnings(image_count))
