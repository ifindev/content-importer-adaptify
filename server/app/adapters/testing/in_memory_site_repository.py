from app.core.domain.models import Site


class InMemorySiteRepository:
    def __init__(self) -> None:
        self._sites: dict[str, Site] = {}

    def list_sites(self) -> list[Site]:
        return list(self._sites.values())

    def create_site(self, site: Site) -> Site:
        self._sites[site.id] = site
        return site

    def save_site(self, site: Site) -> Site:
        self._sites[site.id] = site
        return site

    def get_site(self, site_id: str) -> Site | None:
        return self._sites.get(site_id)

    def delete_site(self, site_id: str) -> None:
        self._sites.pop(site_id, None)

    def find_site_id_by_review_token_hash(self, token_hash: str) -> str | None:
        for site_id, site in self._sites.items():
            if site.review_token_hash == token_hash:
                return site_id
        return None
