from datetime import datetime

from app.core.domain.errors import WordPressError
from app.core.domain.models import PostStatus


class ScriptedPublisher:
    def __init__(self) -> None:
        self.created: list[dict] = []
        self.updated: list[dict] = []
        self.drafted: list[int] = []
        self.find_by_slug_calls: list[str] = []
        self.create_error: WordPressError | None = None
        self.update_error: WordPressError | None = None
        self.find_by_slug_result: int | None = None
        self.get_statuses_result: list[PostStatus] = []
        self.get_statuses_error: WordPressError | None = None
        self.check_credentials_error: WordPressError | None = None
        self._next_id = 1

    async def check_credentials(self) -> None:
        if self.check_credentials_error is not None:
            raise self.check_credentials_error

    async def create_scheduled(
        self, title: str, slug: str, html: str, publish_at_utc: datetime
    ) -> int:
        if self.create_error is not None:
            raise self.create_error
        self.created.append(
            {"title": title, "slug": slug, "html": html, "publish_at_utc": publish_at_utc}
        )
        wp_post_id = self._next_id
        self._next_id += 1
        return wp_post_id

    async def update_scheduled(
        self,
        wp_post_id: int,
        *,
        title: str | None = None,
        slug: str | None = None,
        html: str | None = None,
        publish_at_utc: datetime | None = None,
        status: str | None = None,
    ) -> None:
        if self.update_error is not None:
            raise self.update_error
        self.updated.append(
            {
                "wp_post_id": wp_post_id,
                "title": title,
                "slug": slug,
                "html": html,
                "publish_at_utc": publish_at_utc,
                "status": status,
            }
        )

    async def set_draft(self, wp_post_id: int) -> None:
        self.drafted.append(wp_post_id)

    async def find_by_slug(self, slug: str) -> int | None:
        self.find_by_slug_calls.append(slug)
        return self.find_by_slug_result

    async def get_statuses(self, post_ids: list[int]) -> list[PostStatus]:
        if self.get_statuses_error is not None:
            raise self.get_statuses_error
        return self.get_statuses_result
