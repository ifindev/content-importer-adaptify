import logging
from dataclasses import dataclass, field

from cryptography.fernet import Fernet
from google.cloud import firestore
from google.cloud.firestore import Client

from app.adapters.clock import SystemClock
from app.adapters.crypto.fernet_cipher import FernetCredentialCipher
from app.adapters.documents.parser import RealDocumentParser
from app.adapters.firestore.repository import FirestoreArticleRepository
from app.adapters.firestore.site_repository import FirestoreSiteRepository
from app.adapters.testing.in_memory_repository import InMemoryArticleRepository
from app.adapters.testing.in_memory_site_repository import InMemorySiteRepository
from app.adapters.wordpress.publisher import WordPressPublisher
from app.core.domain.models import Site
from app.core.ports.article_repository import ArticleRepository
from app.core.ports.clock import Clock
from app.core.ports.credential_cipher import CredentialCipher
from app.core.ports.document_parser import DocumentParser
from app.core.ports.publisher import Publisher
from app.core.ports.site_repository import SiteRepository
from app.core.use_cases.sync_status import SyncCache
from app.settings import Settings

logger = logging.getLogger(__name__)


@dataclass
class Container:
    clock: Clock
    document_parser: DocumentParser
    web_base_url: str
    sync_cache: SyncCache
    site_repository: SiteRepository
    credential_cipher: CredentialCipher
    firestore_client: Client | None
    internal_api_secret: str = ""
    # Empty means any Firebase account may sign in; allowed outside prod only.
    agency_emails: frozenset[str] = frozenset()
    # http:// WordPress URLs send the app password unencrypted; local only.
    allow_http_wordpress: bool = False
    _in_memory_repos: dict[str, ArticleRepository] = field(default_factory=dict, repr=False)

    def repository_for(self, site_id: str) -> ArticleRepository:
        if self.firestore_client is not None:
            return FirestoreArticleRepository(self.firestore_client, site_id=site_id)
        return self._in_memory_repos.setdefault(
            site_id,
            InMemoryArticleRepository(site_id=site_id, site_repository=self.site_repository),
        )

    def delete_site(self, site_id: str) -> None:
        """Removes the site and its articles. Firestore cascades the
        subcollections; the in-memory fallback keeps articles here."""
        self.site_repository.delete_site(site_id)
        self._in_memory_repos.pop(site_id, None)

    def build_publisher_from_credentials(
        self, base_url: str, username: str, app_password: str
    ) -> Publisher:
        return WordPressPublisher(base_url=base_url, username=username, app_password=app_password)

    def publisher_for(self, site: Site) -> Publisher:
        password = self.credential_cipher.decrypt(site.wp_app_password_encrypted)
        return self.build_publisher_from_credentials(site.wp_base_url, site.wp_username, password)


def build_container(settings: Settings) -> Container:
    encryption_key = settings.credential_encryption_key
    if not encryption_key:
        if settings.app_env == "prod":
            raise RuntimeError("CREDENTIAL_ENCRYPTION_KEY is required when APP_ENV=prod")
        encryption_key = Fernet.generate_key().decode()
        logger.warning(
            "CREDENTIAL_ENCRYPTION_KEY not set; generated a one-off key for this process. "
            "Site credentials encrypted now won't decrypt after a restart — set "
            "CREDENTIAL_ENCRYPTION_KEY in .env for local persistence."
        )

    if settings.app_env == "prod" and not settings.internal_api_secret:
        raise RuntimeError("INTERNAL_API_SECRET is required when APP_ENV=prod")

    agency_emails = frozenset(
        e.strip().lower() for e in settings.agency_emails.split(",") if e.strip()
    )
    if settings.app_env == "prod" and not agency_emails:
        raise RuntimeError("AGENCY_EMAILS is required when APP_ENV=prod")

    try:
        firestore_client: Client | None = firestore.Client()
    except Exception as exc:
        if settings.app_env == "prod":
            raise
        logger.error(
            "Firestore unavailable (%s); falling back to in-memory repositories. Check "
            "FIRESTORE_EMULATOR_HOST/GOOGLE_CLOUD_PROJECT in .env. The API will keep running.",
            exc,
        )
        firestore_client = None

    site_repository: SiteRepository = (
        FirestoreSiteRepository(firestore_client)
        if firestore_client is not None
        else InMemorySiteRepository()
    )

    return Container(
        clock=SystemClock(),
        document_parser=RealDocumentParser(),
        web_base_url=settings.web_base_url,
        sync_cache=SyncCache(),
        site_repository=site_repository,
        credential_cipher=FernetCredentialCipher(encryption_key),
        firestore_client=firestore_client,
        allow_http_wordpress=settings.app_env != "prod",
        internal_api_secret=settings.internal_api_secret,
        agency_emails=agency_emails,
    )
