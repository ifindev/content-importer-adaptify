import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class LocalFileSecretStore:
    def __init__(self, path: Path) -> None:
        self._path = path

    def get_review_token(self, site_id: str) -> str | None:
        if not self._path.exists():
            return None
        return json.loads(self._path.read_text()).get("review_tokens", {}).get(site_id)

    def set_review_token(self, site_id: str, token: str) -> None:
        data = json.loads(self._path.read_text()) if self._path.exists() else {}
        data.setdefault("review_tokens", {})[site_id] = token
        self._path.write_text(json.dumps(data))
        logger.info(
            "Local secret store: review token written for site %s to %s", site_id, self._path
        )
