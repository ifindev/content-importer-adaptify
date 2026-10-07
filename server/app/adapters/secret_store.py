import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class LocalFileSecretStore:
    def __init__(self, path: Path) -> None:
        self._path = path

    def get_review_token(self) -> str | None:
        if not self._path.exists():
            return None
        return json.loads(self._path.read_text()).get("review_token")

    def set_review_token(self, token: str) -> None:
        self._path.write_text(json.dumps({"review_token": token}))
        logger.info("Local secret store: review token written to %s", self._path)
