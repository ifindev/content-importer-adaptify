from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.core.domain.statuses import EventType, Status, SyncWarning

PostStatusValue = Literal["publish", "future", "draft", "private"]


@dataclass(frozen=True)
class PostStatus:
    id: int
    status: PostStatusValue
    link: str | None
    date_gmt: datetime | None


ArticleSource = Literal["paste", "docx"]


class Site(BaseModel):
    name: str
    wp_base_url: str
    review_token_hash: str | None = None
    review_token_created_at: datetime | None = None


class Article(BaseModel):
    id: str
    title: str
    slug: str
    body_html: str
    source: ArticleSource
    source_filename: str | None = None
    warnings: list[str] = []
    status: Status
    sync_warning: SyncWarning | None = None
    version: int
    approved_version: int | None = None
    publish_at_utc: datetime | None = None
    wp_post_id: int | None = None
    published_url: str | None = None
    last_error: str | None = None
    last_checked_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class Event(BaseModel):
    id: str
    type: EventType
    actor: str
    at: datetime
    data: dict | None = None
