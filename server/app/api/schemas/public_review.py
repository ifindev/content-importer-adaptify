from datetime import datetime

from pydantic import BaseModel, Field

from app.core.domain.statuses import Status, SyncWarning


class ArticleCard(BaseModel):
    id: str = Field(..., description="Article id.")
    title: str = Field(..., description="Article title.")
    slug: str = Field(..., description="URL slug.")
    published_url: str | None = Field(None, description="Live URL, once published.")
    publish_at_utc: datetime | None = Field(None, description="Scheduled publish time, UTC.")
    sync_warning: SyncWarning | None = Field(
        None, description="Warning from the last WordPress status check, if any."
    )
    sent_for_review_at: datetime | None = Field(
        None, description="When the agency last sent it for review, UTC."
    )


class ReviewPageOut(BaseModel):
    site_name: str = Field(..., description="The site's name.")
    waiting: list[ArticleCard] = Field(..., description="Awaiting the client's review.")
    upcoming: list[ArticleCard] = Field(..., description="Scheduled to publish.")
    published: list[ArticleCard] = Field(..., description="Already live.")
    wordpress_unreachable: bool = Field(
        ..., description="True if the last WordPress status check failed."
    )


class ReviewArticleOut(BaseModel):
    id: str = Field(..., description="Article id.")
    title: str = Field(..., description="Article title.")
    slug: str = Field(..., description="URL slug.")
    body_html: str = Field(..., description="Article body, as HTML.")
    version: int = Field(..., description="Increments on every body edit.")
    status: Status = Field(..., description="Current lifecycle status.")
    sent_for_review_at: datetime | None = Field(
        None, description="When the agency last sent it for review, UTC."
    )


class ApproveRequest(BaseModel):
    client_name: str = Field(..., min_length=1, max_length=100, description="The client's name.")
    version: int = Field(..., description="The version the client is approving.")


class RequestChangesRequest(BaseModel):
    client_name: str = Field(..., min_length=1, max_length=100, description="The client's name.")
    comment: str = Field(
        ..., min_length=1, max_length=2000, description="What the client wants changed."
    )
    version: int = Field(..., description="The version the client is reading.")


class ReviewActionOut(BaseModel):
    id: str = Field(..., description="Article id.")
    status: Status = Field(..., description="Status after the action.")
