import logging

from google.cloud.firestore import Client, Query
from google.cloud.firestore_v1.base_query import FieldFilter

from app.core.domain.models import Article, Event, Site
from app.core.domain.statuses import Status

logger = logging.getLogger(__name__)


class FirestoreArticleRepository:
    def __init__(self, client: Client, site_id: str) -> None:
        self._client = client
        self._site_id = site_id

    @property
    def _site_ref(self):
        return self._client.collection("sites").document(self._site_id)

    def _articles_ref(self):
        return self._site_ref.collection("articles")

    def _events_ref(self, article_id: str):
        return self._articles_ref().document(article_id).collection("events")

    def ensure_site_bootstrapped(self, name: str, wp_base_url: str) -> Site:
        snapshot = self._site_ref.get()
        if snapshot.exists:
            logger.info("Firestore site %s already bootstrapped", self._site_id)
            return Site(**snapshot.to_dict())

        site = Site(name=name, wp_base_url=wp_base_url)
        self._site_ref.set(site.model_dump())
        logger.info("Firestore site %s bootstrapped from config", self._site_id)
        return site

    def get_site(self) -> Site:
        snapshot = self._site_ref.get()
        logger.info("Firestore get site %s -> exists=%s", self._site_id, snapshot.exists)
        return Site(**snapshot.to_dict())

    def list_articles(self, status: Status | None = None) -> list[Article]:
        query = self._articles_ref()
        if status is not None:
            query = query.where(filter=FieldFilter("status", "==", status.value))
        query = query.order_by("created_at", direction=Query.DESCENDING)
        articles = [Article(id=doc.id, **doc.to_dict()) for doc in query.stream()]
        logger.info("Firestore list_articles status=%s -> %s articles", status, len(articles))
        return articles

    def get_article(self, article_id: str) -> Article | None:
        snapshot = self._articles_ref().document(article_id).get()
        logger.info("Firestore get_article %s -> exists=%s", article_id, snapshot.exists)
        if not snapshot.exists:
            return None
        return Article(id=snapshot.id, **snapshot.to_dict())

    def create_article(self, article: Article) -> Article:
        self._articles_ref().document(article.id).set(article.model_dump(exclude={"id"}))
        logger.info("Firestore create_article %s status=%s", article.id, article.status)
        return article

    def save_article(self, article: Article, event: Event | None = None) -> Article:
        batch = self._client.batch()
        batch.set(self._articles_ref().document(article.id), article.model_dump(exclude={"id"}))
        if event is not None:
            batch.set(
                self._events_ref(article.id).document(event.id), event.model_dump(exclude={"id"})
            )
        batch.commit()
        logger.info(
            "Firestore save_article %s status=%s event=%s",
            article.id,
            article.status,
            event.type if event else None,
        )
        return article

    def list_events(self, article_id: str) -> list[Event]:
        query = self._events_ref(article_id).order_by("at")
        events = [Event(id=doc.id, **doc.to_dict()) for doc in query.stream()]
        logger.info("Firestore list_events %s -> %s events", article_id, len(events))
        return events
