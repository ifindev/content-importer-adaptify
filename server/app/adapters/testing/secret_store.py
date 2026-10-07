class InMemorySecretStore:
    def __init__(self) -> None:
        self._review_token: str | None = None

    def get_review_token(self) -> str | None:
        return self._review_token

    def set_review_token(self, token: str) -> None:
        self._review_token = token
