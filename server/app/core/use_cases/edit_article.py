import uuid

from app.core.domain import lifecycle
from app.core.domain.errors import NotEditableError
from app.core.domain.models import Article, Event
from app.core.domain.statuses import EventType, Status
from app.core.ports.article_repository import ArticleRepository
from app.core.ports.clock import Clock
from app.core.ports.document_parser import DocumentParser

# Scheduled is read-only, like Awaiting approval: the agency unschedules it
# (back to Approved) first, so editing never has to touch WordPress.
EDITABLE_STATUSES = {Status.DRAFT, Status.CHANGES_REQUESTED, Status.APPROVED}


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
    reset = article.status == Status.APPROVED
    data = {"reset_from": Status.APPROVED.value} if reset else None
    if reset:
        # Edits reset approval: the client approves the text that goes live.
        updated, event = lifecycle.transition(
            article, Status.DRAFT, actor, EventType.EDITED, now, data
        )
    else:
        updated = article
        event = Event(id=str(uuid.uuid4()), type=EventType.EDITED, actor=actor, at=now)

    updates: dict = {"version": article.version + 1, "updated_at": now, "client_comment": None}
    if reset:
        updates["approved_version"] = None
    if title is not None:
        updates["title"] = title
    if slug is not None:
        updates["slug"] = slug
    if body_html is not None:
        updates["body_html"] = parser.clean_html(body_html).body_html

    updated = updated.model_copy(update=updates)
    repository.save_article(updated, event)
    return updated
