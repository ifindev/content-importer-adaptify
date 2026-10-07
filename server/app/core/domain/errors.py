class WordPressError(Exception):
    def __init__(self, http_status: int, code: str, message: str = "") -> None:
        self.http_status = http_status
        self.code = code
        self.message = message
        super().__init__(f"WordPress error {http_status} ({code}): {message}")
