import logging
from dataclasses import dataclass
from pathlib import Path

from google.cloud import firestore

from app.adapters.clock import SystemClock
from app.adapters.documents.parser import RealDocumentParser
from app.adapters.firestore.repository import FirestoreArticleRepository
from app.adapters.secret_store import LocalFileSecretStore
from app.adapters.testing.in_memory_repository import InMemoryArticleRepository
from app.adapters.wordpress.publisher import WordPressPublisher
from app.core.ports.article_repository import ArticleRepository
from app.core.ports.clock import Clock
from app.core.ports.document_parser import DocumentParser
from app.core.ports.publisher import Publisher
from app.core.ports.secret_store import SecretStore
from app.settings import Settings

SITE_ID = "default"
SECRET_STORE_PATH = Path(__file__).resolve().parent.parent / ".secrets.local.json"

logger = logging.getLogger(__name__)


@dataclass
class Container:
    clock: Clock
    publisher: Publisher
    article_repository: ArticleRepository
    document_parser: DocumentParser
    secret_store: SecretStore
    web_base_url: str


def build_container(settings: Settings) -> Container:
    try:
        article_repository: ArticleRepository = FirestoreArticleRepository(
            firestore.Client(), site_id=SITE_ID
        )
    except Exception as exc:
        if settings.app_env == "gcp":
            raise
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
        document_parser=RealDocumentParser(),
        secret_store=LocalFileSecretStore(SECRET_STORE_PATH),
        web_base_url=settings.web_base_url,
    )
