import logging
from datetime import UTC
from datetime import datetime as dt

import httpx

from app.core.domain.errors import WordPressError
from app.core.domain.models import PostStatus

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(10.0, read=30.0)  # ponytail: guessed values, tune if WP is slow/flaky


class WordPressPublisher:
    def __init__(
        self,
        base_url: str,
        username: str,
        app_password: str,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._client = httpx.AsyncClient(
            base_url=f"{base_url.rstrip('/')}/wp-json/wp/v2",
            auth=httpx.BasicAuth(username, app_password),
            timeout=_TIMEOUT,
            transport=transport,
        )

    async def check_credentials(self) -> None:
        await self._request("GET", "/users/me", params={"context": "edit"})

    async def create_scheduled(self, title: str, slug: str, html: str, publish_at_utc: dt) -> int:
        body = {
            "title": title,
            "slug": slug,
            "content": html,
            "status": "future",
            "date_gmt": publish_at_utc.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S"),
        }
        data = await self._request("POST", "/posts", json=body)
        post_id = data["id"]
        logger.info(
            "WordPress created post %s: slug=%s status=%s publish_at=%s link=%s",
            post_id,
            data.get("slug"),
            data.get("status"),
            data.get("date_gmt"),
            data.get("link"),
        )
        return post_id

    async def update_scheduled(
        self,
        wp_post_id: int,
        *,
        title: str | None = None,
        slug: str | None = None,
        html: str | None = None,
        publish_at_utc: dt | None = None,
        status: str | None = None,
    ) -> None:
        body = {}
        if title is not None:
            body["title"] = title
        if slug is not None:
            body["slug"] = slug
        if html is not None:
            body["content"] = html
        if publish_at_utc is not None:
            body["date_gmt"] = publish_at_utc.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S")
        if status is not None:
            body["status"] = status
        data = await self._request("POST", f"/posts/{wp_post_id}", json=body)
        logger.info(
            "WordPress updated post %s: slug=%s status=%s publish_at=%s",
            wp_post_id,
            data.get("slug"),
            data.get("status"),
            data.get("date_gmt"),
        )

    async def set_draft(self, wp_post_id: int) -> None:
        await self._request("POST", f"/posts/{wp_post_id}", json={"status": "draft"})
        logger.info("WordPress set post %s to draft", wp_post_id)

    async def find_by_slug(self, slug: str) -> int | None:
        params = {
            "slug": slug,
            "status": "future,draft,publish,private",
            "context": "edit",
        }
        data = await self._request("GET", "/posts", params=params)
        post_id = data[0]["id"] if data else None
        logger.info("WordPress find by slug %s -> %s", slug, post_id)
        return post_id

    async def get_statuses(self, post_ids: list[int]) -> list[PostStatus]:
        params = {
            "include": ",".join(str(i) for i in post_ids),
            "status": "publish,future,draft,private",
            "_fields": "id,status,link,date_gmt",
            "context": "edit",
            "per_page": 100,
        }
        data = await self._request("GET", "/posts", params=params)
        statuses = [
            PostStatus(
                id=p["id"],
                status=p["status"],
                link=p.get("link"),
                date_gmt=dt.fromisoformat(p["date_gmt"]).replace(tzinfo=UTC)
                if p.get("date_gmt")
                else None,
            )
            for p in data
        ]
        logger.info(
            "WordPress statuses for %s: %s",
            post_ids,
            [{"id": s.id, "status": s.status, "link": s.link} for s in statuses],
        )
        return statuses

    async def _request(self, method: str, path: str, **kwargs) -> dict | list:
        try:
            response = await self._client.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            logger.error(
                "WordPress %s %s failed (%s): %s", method, path, self._client.base_url, exc
            )
            raise WordPressError(0, "transport_error", str(exc)) from exc
        if response.is_error:
            try:
                body = response.json()
                code = body.get("code", "unknown_error")
                message = body.get("message", "")
            except Exception:
                code, message = "unknown_error", response.text
            logger.error("WordPress %s %s -> %s %s", method, path, response.status_code, code)
            raise WordPressError(response.status_code, code, message)
        logger.info("WordPress %s %s -> %s", method, path, response.status_code)
        return response.json()
