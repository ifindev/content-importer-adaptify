class InMemorySecretStore:
    def __init__(self) -> None:
        self._review_tokens: dict[str, str] = {}

    def get_review_token(self, site_id: str) -> str | None:
        return self._review_tokens.get(site_id)

    def set_review_token(self, site_id: str, token: str) -> None:
        self._review_tokens[site_id] = token
