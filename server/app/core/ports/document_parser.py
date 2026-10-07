from typing import Protocol

from pydantic import BaseModel


class ParsedDocument(BaseModel):
    title: str | None
    body_html: str
    warnings: list[str] = []


class DocumentParser(Protocol):
    def clean_html(self, html: str) -> ParsedDocument: ...

    def parse_docx(self, content: bytes, filename: str) -> ParsedDocument: ...
