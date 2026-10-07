from typing import Protocol


class SecretStore(Protocol):
    def get_review_token(self) -> str | None: ...

    def set_review_token(self, token: str) -> None: ...
