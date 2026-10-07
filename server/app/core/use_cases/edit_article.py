import uuid

from app.core.domain.errors import NotEditableError
from app.core.domain.models import Article, Event
from app.core.domain.statuses import EventType, Status
from app.core.ports.article_repository import ArticleRepository
from app.core.ports.clock import Clock
from app.core.ports.document_parser import DocumentParser

EDITABLE_STATUSES = {Status.DRAFT, Status.CHANGES_REQUESTED, Status.APPROVED, Status.SCHEDULED}
RESET_STATUSES = {Status.APPROVED, Status.SCHEDULED}


def edit_article(
    article: Article,
    title: str | None,
    slug: str | None,
    body_html: str | None,
    repository: ArticleRepository,
    parser: DocumentParser,
    clock: Clock,
    actor: str,
) -> Article:
    if article.status not in EDITABLE_STATUSES:
        raise NotEditableError(article.status)

    now = clock.now()
    reset_from = article.status.value if article.status in RESET_STATUSES else None

    updates: dict = {"version": article.version + 1, "updated_at": now, "client_comment": None}
    if reset_from is not None:
        updates["status"] = Status.DRAFT
    if title is not None:
        updates["title"] = title
    if slug is not None:
        updates["slug"] = slug
    if body_html is not None:
        updates["body_html"] = parser.clean_html(body_html).body_html

    updated = article.model_copy(update=updates)
    event = Event(
        id=str(uuid.uuid4()),
        type=EventType.EDITED,
        actor=actor,
        at=now,
        data={"reset_from": reset_from} if reset_from else None,
    )
    repository.save_article(updated, event)
    return updated
