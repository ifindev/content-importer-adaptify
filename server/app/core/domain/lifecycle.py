import uuid
from datetime import datetime

from app.core.domain.errors import NotAllowed
from app.core.domain.models import Article, Event
from app.core.domain.statuses import EventType, Status

ALLOWED_TRANSITIONS: dict[Status, set[Status]] = {
    Status.DRAFT: {Status.AWAITING_APPROVAL},
    Status.AWAITING_APPROVAL: {Status.DRAFT, Status.CHANGES_REQUESTED, Status.APPROVED},
    Status.CHANGES_REQUESTED: {Status.AWAITING_APPROVAL},
    Status.APPROVED: {Status.SCHEDULED, Status.FAILED, Status.DRAFT},
    # Read-only: the agency unschedules (back to Approved) before editing.
    # Failed covers a date change WordPress refused.
    Status.SCHEDULED: {Status.PUBLISHED, Status.APPROVED, Status.FAILED},
    Status.FAILED: {Status.SCHEDULED},
    Status.PUBLISHED: set(),
}


def transition(
    article: Article,
    to_status: Status,
    actor: str,
    event_type: EventType,
    at: datetime,
    data: dict | None = None,
) -> tuple[Article, Event]:
    if to_status not in ALLOWED_TRANSITIONS[article.status]:
        raise NotAllowed(article.status, to_status)

    event = Event(id=str(uuid.uuid4()), type=event_type, actor=actor, at=at, data=data)
    updated = article.model_copy(update={"status": to_status, "updated_at": at})
    return updated, event
