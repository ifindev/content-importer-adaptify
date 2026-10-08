from app.core.domain.errors import NotDeletableError
from app.core.domain.models import Article
from app.core.domain.statuses import Status
from app.core.ports.article_repository import ArticleRepository

# Only articles that never reached WordPress, so there is nothing to clean up there.
DELETABLE_STATUSES = {Status.DRAFT, Status.CHANGES_REQUESTED}


def delete_article(article: Article, repository: ArticleRepository) -> None:
    if article.status not in DELETABLE_STATUSES:
        raise NotDeletableError(article.status)
    repository.delete_article(article.id)
