from app.core.domain.errors import NotDeletableError
from app.core.domain.models import Article
from app.core.domain.statuses import Status
from app.core.ports.article_repository import ArticleRepository
from app.core.ports.publisher import Publisher

# Never published or scheduled now. Unschedule trashes its post, so this is
# only for older data that still owns a WordPress draft; it goes to the trash.
DELETABLE_STATUSES = {Status.DRAFT, Status.CHANGES_REQUESTED}


async def delete_article(
    article: Article, repository: ArticleRepository, publisher: Publisher
) -> None:
    if article.status not in DELETABLE_STATUSES:
        raise NotDeletableError(article.status)
    if article.wp_post_id is not None:
        # First, so a WordPress refusal deletes nothing.
        await publisher.trash_post(article.wp_post_id)
    repository.delete_article(article.id)
