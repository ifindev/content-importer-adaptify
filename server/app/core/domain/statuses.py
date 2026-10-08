from enum import StrEnum


class Status(StrEnum):
    DRAFT = "draft"
    AWAITING_APPROVAL = "awaiting_approval"
    CHANGES_REQUESTED = "changes_requested"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


class SyncWarning(StrEnum):
    LATE = "late"
    CHANGED_IN_WORDPRESS = "changed_in_wordpress"
    MISSING_IN_WORDPRESS = "missing_in_wordpress"


class EventType(StrEnum):
    IMPORTED = "imported"
    EDITED = "edited"
    SENT_FOR_REVIEW = "sent_for_review"
    PULLED_BACK = "pulled_back"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    SCHEDULED = "scheduled"
    DATE_CHANGED = "date_changed"
    PUBLISHED = "published"
    FAILED = "failed"
    RETRIED = "retried"
    UNSCHEDULED = "unscheduled"
    AI_DRAFT_CREATED = "ai_draft_created"
    AI_DRAFT_ACCEPTED = "ai_draft_accepted"
