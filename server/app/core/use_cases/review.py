import hmac

from app.core.domain.models import Article, Site
from app.core.domain.statuses import Status
from app.core.lib.tokens import hash_token
from app.core.ports.article_repository import ArticleRepository

VISIBLE_STATUSES = {Status.AWAITING_APPROVAL, Status.SCHEDULED, Status.PUBLISHED}


class InvalidTokenError(Exception):
    pass


class ArticleNotVisibleError(Exception):
    pass


def _verify_token(site: Site, token: str) -> None:
    if site.review_token_hash is None or not hmac.compare_digest(
        hash_token(token), site.review_token_hash
    ):
        raise InvalidTokenError


def get_review_page(
    repository: ArticleRepository, token: str
) -> tuple[Site, dict[Status, list[Article]]]:
    site = repository.get_site()
    _verify_token(site, token)

    groups: dict[Status, list[Article]] = {status: [] for status in VISIBLE_STATUSES}
    for article in repository.list_articles():
        if article.status in VISIBLE_STATUSES:
            groups[article.status].append(article)
    return site, groups


def get_review_article(repository: ArticleRepository, token: str, article_id: str) -> Article:
    site = repository.get_site()
    _verify_token(site, token)

    article = repository.get_article(article_id)
    if article is None or article.status not in VISIBLE_STATUSES:
        raise ArticleNotVisibleError
    return article
