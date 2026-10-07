from typing import Protocol


class SecretStore(Protocol):
    def get_review_token(self, site_id: str) -> str | None: ...

    def set_review_token(self, site_id: str, token: str) -> None: ...
