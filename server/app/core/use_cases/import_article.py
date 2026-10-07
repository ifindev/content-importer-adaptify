import uuid

from app.core.domain.errors import EmptyContentError
from app.core.domain.models import Article, Event
from app.core.domain.statuses import EventType, Status
from app.core.lib.slug import slugify
from app.core.ports.article_repository import ArticleRepository
from app.core.ports.clock import Clock
from app.core.ports.document_parser import DocumentParser


def _save_imported(
    title: str,
    body_html: str,
    warnings: list[str],
    source: str,
    source_filename: str | None,
    repository: ArticleRepository,
    clock: Clock,
    actor: str,
) -> Article:
    now = clock.now()
    article = Article(
        id=str(uuid.uuid4()),
        title=title,
        slug=slugify(title),
        body_html=body_html,
        source=source,
        source_filename=source_filename,
        warnings=warnings,
        status=Status.DRAFT,
        version=1,
        created_at=now,
        updated_at=now,
    )
    repository.create_article(article)
    event = Event(id=str(uuid.uuid4()), type=EventType.IMPORTED, actor=actor, at=now)
    repository.save_article(article, event)
    return article


def import_from_paste(
    html: str,
    repository: ArticleRepository,
    parser: DocumentParser,
    clock: Clock,
    actor: str,
) -> Article:
    parsed = parser.clean_html(html)
    if not parsed.body_html.strip():
        raise EmptyContentError
    title = parsed.title or "Untitled"
    return _save_imported(
        title, parsed.body_html, parsed.warnings, "paste", None, repository, clock, actor
    )


def import_from_docx(
    filename: str,
    content: bytes,
    repository: ArticleRepository,
    parser: DocumentParser,
    clock: Clock,
    actor: str,
) -> Article:
    parsed = parser.parse_docx(content, filename)
    title = parsed.title or filename.rsplit(".", 1)[0]
    return _save_imported(
        title, parsed.body_html, parsed.warnings, "docx", filename, repository, clock, actor
    )
