from datetime import datetime

from app.core.lib.tokens import generate_token, hash_token
from app.core.ports.article_repository import ArticleRepository
from app.core.ports.clock import Clock
from app.core.ports.secret_store import SecretStore


def get_or_create_review_link(
    repository: ArticleRepository,
    secret_store: SecretStore,
    clock: Clock,
    web_base_url: str,
) -> tuple[str, datetime]:
    token = secret_store.get_review_token()
    if token is None:
        token, created_at = _rotate(repository, secret_store, clock)
    else:
        created_at = repository.get_site().review_token_created_at or clock.now()
    return f"{web_base_url}/review/{token}", created_at


def reset_review_link(
    repository: ArticleRepository,
    secret_store: SecretStore,
    clock: Clock,
    web_base_url: str,
) -> tuple[str, datetime]:
    token, created_at = _rotate(repository, secret_store, clock)
    return f"{web_base_url}/review/{token}", created_at


def _rotate(
    repository: ArticleRepository, secret_store: SecretStore, clock: Clock
) -> tuple[str, datetime]:
    token = generate_token()
    created_at = clock.now()
    site = repository.get_site()
    updates = {"review_token_hash": hash_token(token), "review_token_created_at": created_at}
    repository.save_site(site.model_copy(update=updates))
    secret_store.set_review_token(token)
    return token, created_at
