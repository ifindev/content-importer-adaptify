from datetime import datetime
from typing import Protocol

from app.core.domain.models import PostStatus


class Publisher(Protocol):
    async def check_credentials(self) -> None: ...

    async def create_scheduled(
        self, title: str, slug: str, html: str, publish_at_utc: datetime
    ) -> int: ...

    async def get_statuses(self, post_ids: list[int]) -> list[PostStatus]: ...
