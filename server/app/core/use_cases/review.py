import hmac

from app.core.domain import lifecycle
from app.core.domain.errors import (
    ArticleChangedError,
    ArticleNotVisibleError,
    InvalidTokenError,
    NotAwaitingApprovalError,
    NotSendableError,
)
from app.core.domain.models import Article, Site
from app.core.domain.statuses import EventType, Status
from app.core.lib.tokens import hash_token
from app.core.ports.article_repository import ArticleRepository
from app.core.ports.clock import Clock

VISIBLE_STATUSES = {Status.AWAITING_APPROVAL, Status.SCHEDULED, Status.PUBLISHED}
SENDABLE_STATUSES = {Status.DRAFT, Status.CHANGES_REQUESTED}


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


def send_for_review(
    article: Article, repository: ArticleRepository, clock: Clock, actor: str
) -> Article:
    if article.status not in SENDABLE_STATUSES:
        raise NotSendableError(article.status)
    updated, event = lifecycle.transition(
        article, Status.AWAITING_APPROVAL, actor, EventType.SENT_FOR_REVIEW, clock.now()
    )
    updated = updated.model_copy(update={"client_comment": None, "sent_for_review_at": event.at})
    repository.save_article(updated, event)
    return updated


def pull_back(article: Article, repository: ArticleRepository, clock: Clock, actor: str) -> Article:
    if article.status != Status.AWAITING_APPROVAL:
        raise NotAwaitingApprovalError(article.status)
    updated, event = lifecycle.transition(
        article, Status.DRAFT, actor, EventType.PULLED_BACK, clock.now()
    )
    repository.save_article(updated, event)
    return updated


def _get_awaiting_approval_article(
    repository: ArticleRepository, token: str, article_id: str, version: int
) -> Article:
    site = repository.get_site()
    _verify_token(site, token)

    article = repository.get_article(article_id)
    if article is None:
        raise ArticleNotVisibleError
    if article.status != Status.AWAITING_APPROVAL:
        raise NotAwaitingApprovalError(article.status)
    if article.version != version:
        raise ArticleChangedError(article.version, version)
    return article


def approve(
    repository: ArticleRepository,
    clock: Clock,
    token: str,
    article_id: str,
    client_name: str,
    version: int,
) -> Article:
    article = _get_awaiting_approval_article(repository, token, article_id, version)
    updated, event = lifecycle.transition(
        article, Status.APPROVED, client_name, EventType.APPROVED, clock.now()
    )
    updated = updated.model_copy(update={"approved_version": version, "client_comment": None})
    repository.save_article(updated, event)
    return updated


def request_changes(
    repository: ArticleRepository,
    clock: Clock,
    token: str,
    article_id: str,
    client_name: str,
    comment: str,
    version: int,
) -> Article:
    article = _get_awaiting_approval_article(repository, token, article_id, version)
    updated, event = lifecycle.transition(
        article,
        Status.CHANGES_REQUESTED,
        client_name,
        EventType.CHANGES_REQUESTED,
        clock.now(),
        data={"comment": comment},
    )
    updated = updated.model_copy(update={"client_comment": comment})
    repository.save_article(updated, event)
    return updated
