import logging

from google.cloud.firestore import Client
from google.cloud.firestore_v1.base_query import FieldFilter

from app.core.domain.models import Site

logger = logging.getLogger(__name__)


class FirestoreSiteRepository:
    def __init__(self, client: Client) -> None:
        self._client = client

    def _sites_ref(self):
        return self._client.collection("sites")

    def list_sites(self) -> list[Site]:
        sites = [Site(id=doc.id, **doc.to_dict()) for doc in self._sites_ref().stream()]
        logger.info("Firestore list_sites -> %s sites", len(sites))
        return sites

    def create_site(self, site: Site) -> Site:
        self._sites_ref().document(site.id).set(site.model_dump(exclude={"id"}))
        logger.info("Firestore create_site %s", site.id)
        return site

    def save_site(self, site: Site) -> Site:
        self._sites_ref().document(site.id).set(site.model_dump(exclude={"id"}))
        logger.info("Firestore save_site %s", site.id)
        return site

    def get_site(self, site_id: str) -> Site | None:
        snapshot = self._sites_ref().document(site_id).get()
        if not snapshot.exists:
            return None
        return Site(id=snapshot.id, **snapshot.to_dict())

    def delete_site(self, site_id: str) -> None:
        # Removes the site document and every subcollection under it
        # (articles and their events).
        self._client.recursive_delete(self._sites_ref().document(site_id))
        logger.info("Firestore delete_site %s", site_id)

    def find_site_id_by_review_token_hash(self, token_hash: str) -> str | None:
        query = self._sites_ref().where(filter=FieldFilter("review_token_hash", "==", token_hash))
        docs = list(query.limit(1).stream())
        return docs[0].id if docs else None
