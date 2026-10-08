from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.core.domain.statuses import Status


class ChangeRoundsEntry(BaseModel):
    article_id: str = Field(..., description="Article id.")
    title: str = Field(..., description="Article title.")
    rounds: int = Field(..., description="Number of change-request rounds.")


class UpcomingEntry(BaseModel):
    article_id: str = Field(..., description="Article id.")
    title: str = Field(..., description="Article title.")
    publish_at_utc: datetime = Field(..., description="Scheduled publish time, UTC.")


class PublishedEntry(BaseModel):
    article_id: str = Field(..., description="Article id.")
    title: str = Field(..., description="Article title.")
    published_url: str = Field(..., description="Live URL.")
    published_at: datetime = Field(..., description="When the article went live, UTC.")


class NeedsAttentionEntry(BaseModel):
    article_id: str = Field(..., description="Article id.")
    title: str = Field(..., description="Article title.")
    reason: Literal["failed", "late", "changed_in_wordpress", "missing_in_wordpress"] = Field(
        ..., description="Why this article needs attention."
    )
    detail: str | None = Field(None, description="Error detail, for a failed article.")


class ReportOut(BaseModel):
    status_counts: dict[Status, int] = Field(..., description="Article count per status.")
    published_this_month: int = Field(..., description="Published this calendar month, UTC.")
    avg_approval_seconds: float | None = Field(
        None, description="Average sent-for-review-to-approved seconds; null if none approved."
    )
    avg_change_rounds: float | None = Field(
        None, description="Change requests per article, over all articles; null if none."
    )
    change_rounds: list[ChangeRoundsEntry] = Field(
        ..., description="Articles that needed changes, with rounds per article."
    )
    upcoming: list[UpcomingEntry] = Field(..., description="Scheduled articles, soonest first.")
    published: list[PublishedEntry] = Field(
        ..., description="Published articles, most recent first."
    )
    needs_attention: list[NeedsAttentionEntry] = Field(
        ..., description="Failed articles and articles carrying a sync warning."
    )
    wordpress_unreachable: bool = Field(
        ..., description="True if the last WordPress status check failed."
    )
