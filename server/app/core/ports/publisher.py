from datetime import datetime
from typing import Protocol

from app.core.domain.models import PostStatus


class Publisher(Protocol):
    async def check_credentials(self) -> None: ...

    async def create_scheduled(
        self, title: str, slug: str, html: str, publish_at_utc: datetime
    ) -> int: ...

    async def update_scheduled(
        self,
        wp_post_id: int,
        *,
        title: str | None = None,
        slug: str | None = None,
        html: str | None = None,
        publish_at_utc: datetime | None = None,
        status: str | None = None,
    ) -> None: ...

    async def set_draft(self, wp_post_id: int) -> None: ...

    async def find_by_slug(self, slug: str) -> int | None: ...

    async def get_statuses(self, post_ids: list[int]) -> list[PostStatus]: ...
