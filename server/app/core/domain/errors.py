"""Domain errors raised by use cases, the lifecycle, and adapters.

These classes know nothing about HTTP. ``api/error_handlers.py`` maps them
to a status code and a ``code`` string.
"""


class WordPressError(Exception):
    def __init__(self, http_status: int, code: str, message: str = "") -> None:
        self.http_status = http_status
        self.code = code
        self.message = message
        super().__init__(f"WordPress error {http_status} ({code}): {message}")


class WordPressConnectionTestFailedError(Exception):
    def __init__(self, message: str = "") -> None:
        self.message = message
        super().__init__(f"WordPress connection test failed: {message}")


class NotAllowed(Exception):
    def __init__(self, from_status: str, to_status: str) -> None:
        self.from_status = from_status
        self.to_status = to_status
        super().__init__(f"Cannot move article from {from_status} to {to_status}")


class NotEditableError(Exception):
    def __init__(self, status: str) -> None:
        self.status = status
        super().__init__(f"Article in status {status} is not editable")


class EmptyContentError(Exception):
    pass


class NotSendableError(Exception):
    def __init__(self, status: str) -> None:
        self.status = status
        super().__init__(f"Article in status {status} cannot be sent for review")


class NotAwaitingApprovalError(Exception):
    def __init__(self, status: str) -> None:
        self.status = status
        super().__init__(f"Article in status {status} is not awaiting approval")


class ArticleChangedError(Exception):
    def __init__(self, current_version: int, submitted_version: int) -> None:
        self.current_version = current_version
        self.submitted_version = submitted_version
        super().__init__(
            f"Article is at version {current_version}, but version "
            f"{submitted_version} was submitted"
        )


class NotSchedulableError(Exception):
    def __init__(self, status: str) -> None:
        self.status = status
        super().__init__(f"Article in status {status} cannot be scheduled")


class NotFailedError(Exception):
    def __init__(self, status: str) -> None:
        self.status = status
        super().__init__(f"Article in status {status} is not failed")


class PublishAtInPastError(Exception):
    pass


class InvalidTokenError(Exception):
    pass


class ArticleNotVisibleError(Exception):
    pass


class NotDeletableError(Exception):
    def __init__(self, status: str) -> None:
        self.status = status
        super().__init__(f"Article in status {status} cannot be deleted")
