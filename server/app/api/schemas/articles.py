import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.domain.statuses import EventType, Status, SyncWarning

_SLUG_RE = re.compile(r"[a-z0-9-]+")


class EventOut(BaseModel):
    id: str = Field(..., description="Event id.")
    type: EventType = Field(..., description="What happened.")
    actor: str = Field(..., description="Who or what triggered the event.")
    at: datetime = Field(..., description="When the event happened, UTC.")
    data: dict | None = Field(None, description="The comment or error attached to this event.")


class ArticleSummary(BaseModel):
    id: str = Field(..., description="Article id.")
    title: str = Field(..., description="Article title.")
    slug: str = Field(..., description="URL slug.")
    status: Status = Field(..., description="Current lifecycle status.")
    sync_warning: SyncWarning | None = Field(
        None, description="Warning from the last WordPress status check, if any."
    )
    publish_at_utc: datetime | None = Field(None, description="Scheduled publish time, UTC.")
    updated_at: datetime = Field(..., description="Last update time, UTC.")


class ArticleDetail(BaseModel):
    id: str = Field(..., description="Article id.")
    title: str = Field(..., description="Article title.")
    slug: str = Field(..., description="URL slug.")
    body_html: str = Field(..., description="Article body, as HTML.")
    source: str = Field(..., description="How the article was imported: paste or docx.")
    source_filename: str | None = Field(
        None, description="Original filename, if imported from a file."
    )
    warnings: list[str] = Field([], description="Warnings produced during import.")
    status: Status = Field(..., description="Current lifecycle status.")
    sync_warning: SyncWarning | None = Field(
        None, description="Warning from the last WordPress status check, if any."
    )
    version: int = Field(..., description="Increments on every body edit.")
    approved_version: int | None = Field(None, description="Version the client approved, if any.")
    publish_at_utc: datetime | None = Field(None, description="Scheduled publish time, UTC.")
    wp_post_id: int | None = Field(None, description="WordPress post id, once sent.")
    published_url: str | None = Field(None, description="Live URL, once published.")
    last_error: str | None = Field(None, description="Error from the last failed WordPress call.")
    last_checked_at: datetime | None = Field(None, description="Last WordPress status check time.")
    client_comment: str | None = Field(
        None, description="The client's latest change request, if any."
    )
    created_at: datetime = Field(..., description="Creation time, UTC.")
    updated_at: datetime = Field(..., description="Last update time, UTC.")
    events: list[EventOut] = Field([], description="History log, oldest first.")


class ArticlesOut(BaseModel):
    articles: list[ArticleSummary] = Field(..., description="All matching articles.")
    wordpress_unreachable: bool = Field(
        ..., description="True if the last WordPress status check failed."
    )


class ScheduleRequest(BaseModel):
    publish_at: datetime = Field(
        ..., description="Publish time, as an ISO 8601 datetime with a UTC offset."
    )

    @field_validator("publish_at")
    @classmethod
    def _validate_tz_aware(cls, value: datetime) -> datetime:
        if value.utcoffset() is None:
            raise ValueError("publish_at must include a UTC offset")
        return value


class ArticleUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200, description="New title.")
    slug: str | None = Field(None, description="New slug: lowercase letters, digits, hyphens.")
    body_html: str | None = Field(
        None, min_length=1, description="New body HTML, cleaned like import, capped at 2 MB."
    )

    @field_validator("slug")
    @classmethod
    def _validate_slug(cls, value: str | None) -> str | None:
        if value is not None and not _SLUG_RE.fullmatch(value):
            raise ValueError("slug must be lowercase letters, digits, and hyphens")
        return value
