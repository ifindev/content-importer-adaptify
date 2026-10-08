from datetime import datetime

from app.core.lib.tokens import generate_token, hash_token
from app.core.ports.article_repository import ArticleRepository
from app.core.ports.clock import Clock
from app.core.ports.credential_cipher import CredentialCipher


def get_or_create_review_link(
    repository: ArticleRepository,
    cipher: CredentialCipher,
    clock: Clock,
    web_base_url: str,
) -> tuple[str, datetime]:
    site = repository.get_site()
    # "" when never set, or encrypted under another key: rotate either way.
    token = cipher.decrypt(site.review_token_encrypted) if site.review_token_encrypted else ""
    if not token:
        token, created_at = _rotate(repository, cipher, clock)
    else:
        created_at = site.review_token_created_at or clock.now()
    return f"{web_base_url}/review/{token}", created_at


def reset_review_link(
    repository: ArticleRepository,
    cipher: CredentialCipher,
    clock: Clock,
    web_base_url: str,
) -> tuple[str, datetime]:
    token, created_at = _rotate(repository, cipher, clock)
    return f"{web_base_url}/review/{token}", created_at


def _rotate(
    repository: ArticleRepository, cipher: CredentialCipher, clock: Clock
) -> tuple[str, datetime]:
    token = generate_token()
    created_at = clock.now()
    updates = {
        "review_token_hash": hash_token(token),
        "review_token_encrypted": cipher.encrypt(token),
        "review_token_created_at": created_at,
    }
    repository.save_site(repository.get_site().model_copy(update=updates))
    return token, created_at
