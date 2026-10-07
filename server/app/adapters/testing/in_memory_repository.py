from app.core.domain.models import Article, Event, Site
from app.core.domain.statuses import Status


class InMemoryArticleRepository:
    def __init__(self) -> None:
        self._site: Site | None = None
        self._articles: dict[str, Article] = {}
        self._events: dict[str, list[Event]] = {}

    def ensure_site_bootstrapped(self, name: str, wp_base_url: str) -> Site:
        if self._site is None:
            self._site = Site(name=name, wp_base_url=wp_base_url)
        return self._site

    def get_site(self) -> Site:
        if self._site is None:
            raise RuntimeError("Site not bootstrapped")
        return self._site

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
