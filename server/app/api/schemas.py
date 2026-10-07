from datetime import datetime

from pydantic import BaseModel, Field

from app.core.domain.statuses import EventType, Status, SyncWarning


class SessionRequest(BaseModel):
    id_token: str = Field(
        ...,
        description="Firebase ID token from the client-side sign-in.",
        examples=["eyJhbGciOiJSUzI1NiIsImtpZCI6..."],
    )


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
    created_at: datetime = Field(..., description="Creation time, UTC.")
    updated_at: datetime = Field(..., description="Last update time, UTC.")
    events: list[EventOut] = Field([], description="History log, oldest first.")
