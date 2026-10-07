class WordPressError(Exception):
    def __init__(self, http_status: int, code: str, message: str = "") -> None:
        self.http_status = http_status
        self.code = code
        self.message = message
        super().__init__(f"WordPress error {http_status} ({code}): {message}")


class NotAllowed(Exception):
    def __init__(self, from_status: str, to_status: str) -> None:
        self.from_status = from_status
        self.to_status = to_status
        super().__init__(f"Cannot move article from {from_status} to {to_status}")
