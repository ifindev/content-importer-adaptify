class ArticleNotFoundError(Exception):
    pass


class SiteNotFoundError(Exception):
    pass


class InsecureUrlError(Exception):
    pass


class EmptyUpdateError(Exception):
    pass


class PayloadTooLargeError(Exception):
    pass


class NoFilesError(Exception):
    pass


class TooManyFilesError(Exception):
    pass
