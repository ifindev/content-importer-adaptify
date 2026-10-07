from app.core.domain.models import Article, Event, Site
from app.core.domain.statuses import Status
from app.core.ports.site_repository import SiteRepository


class InMemoryArticleRepository:
    def __init__(
        self, site_id: str | None = None, site_repository: SiteRepository | None = None
    ) -> None:
        # ponytail: a standalone instance keeps its own `_site` (what every
        # existing unit test constructs); Container.repository_for wires
        # site_id/site_repository so the fallback-mode instance reads/writes
        # the same sites/{siteId} record InMemorySiteRepository already owns,
        # instead of a second, disconnected copy of it.
        self._site_id = site_id
        self._site_repository = site_repository
        self._site: Site | None = None
        self._articles: dict[str, Article] = {}
        self._events: dict[str, list[Event]] = {}

    def get_site(self) -> Site:
        if self._site_repository is not None and self._site_id is not None:
            site = self._site_repository.get_site(self._site_id)
            if site is None:
                raise RuntimeError("Site not bootstrapped")
            return site
        if self._site is None:
            raise RuntimeError("Site not bootstrapped")
        return self._site

    def save_site(self, site: Site) -> Site:
        if self._site_repository is not None and self._site_id is not None:
            return self._site_repository.save_site(site)
        self._site = site
        return site

    def list_articles(self, status: Status | None = None) -> list[Article]:
        articles = self._articles.values()
        if status is not None:
            articles = [a for a in articles if a.status == status]
        return sorted(articles, key=lambda a: a.created_at, reverse=True)

    def get_article(self, article_id: str) -> Article | None:
        return self._articles.get(article_id)

    def create_article(self, article: Article) -> Article:
        self._articles[article.id] = article
        self._events[article.id] = []
        return article

    def save_article(self, article: Article, event: Event | None = None) -> Article:
        self._articles[article.id] = article
        if event is not None:
            self._events.setdefault(article.id, []).append(event)
        return article

    def list_events(self, article_id: str) -> list[Event]:
        return list(self._events.get(article_id, []))
