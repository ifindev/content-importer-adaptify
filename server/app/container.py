import logging
from dataclasses import dataclass

from google.cloud import firestore

from app.adapters.clock import SystemClock
from app.adapters.firestore.repository import FirestoreArticleRepository
from app.adapters.testing.in_memory_repository import InMemoryArticleRepository
from app.adapters.wordpress.publisher import WordPressPublisher
from app.core.ports.article_repository import ArticleRepository
from app.core.ports.clock import Clock
from app.core.ports.publisher import Publisher
from app.settings import Settings

SITE_ID = "default"

logger = logging.getLogger(__name__)


@dataclass
class Container:
    clock: Clock
    publisher: Publisher
    article_repository: ArticleRepository


def build_container(settings: Settings) -> Container:
    try:
        article_repository: ArticleRepository = FirestoreArticleRepository(
            firestore.Client(), site_id=SITE_ID
        )
    except Exception as exc:
        logger.error(
            "Firestore unavailable (%s); falling back to an in-memory repository. Check "
            "FIRESTORE_EMULATOR_HOST/GOOGLE_CLOUD_PROJECT in .env. The API will keep running.",
            exc,
        )
        article_repository = InMemoryArticleRepository()

    return Container(
        clock=SystemClock(),
        publisher=WordPressPublisher(
            base_url=settings.wp_base_url,
            username=settings.wp_username,
            app_password=settings.wp_app_password,
        ),
        article_repository=article_repository,
    )
