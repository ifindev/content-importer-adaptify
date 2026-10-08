from dataclasses import dataclass

from fastapi import Request

from app.api.http_errors import SiteNotFoundError
from app.container import Container
from app.core.domain.errors import InvalidTokenError
from app.core.domain.models import Site
from app.core.lib.tokens import hash_token
from app.core.ports.article_repository import ArticleRepository
from app.core.ports.clock import Clock
from app.core.ports.credential_cipher import CredentialCipher
from app.core.ports.document_parser import DocumentParser
from app.core.ports.publisher import Publisher
from app.core.use_cases.sync_status import SyncCache


@dataclass
class SiteContext:
    site_id: str
    site: Site
    repository: ArticleRepository
    publisher: Publisher


def get_site_context(site_id: str, request: Request) -> SiteContext:
    container = request.app.state.container
    site = container.site_repository.get_site(site_id)
    if site is None:
        raise SiteNotFoundError
    return SiteContext(
        site_id=site_id,
        site=site,
        repository=container.repository_for(site_id),
        publisher=container.publisher_for(site),
    )


def get_public_site_context(token: str, request: Request) -> SiteContext:
    container = request.app.state.container
    site_id = container.site_repository.find_site_id_by_review_token_hash(hash_token(token))
    if site_id is None:
        raise InvalidTokenError
    site = container.site_repository.get_site(site_id)
    return SiteContext(
        site_id=site_id,
        site=site,
        repository=container.repository_for(site_id),
        publisher=container.publisher_for(site),
    )


def get_clock(request: Request) -> Clock:
    return request.app.state.container.clock


def get_document_parser(request: Request) -> DocumentParser:
    return request.app.state.container.document_parser


def get_sync_cache(request: Request) -> SyncCache:
    return request.app.state.container.sync_cache


def get_credential_cipher(request: Request) -> CredentialCipher:
    return request.app.state.container.credential_cipher


def get_web_base_url(request: Request) -> str:
    return request.app.state.container.web_base_url


def get_internal_api_secret(request: Request) -> str:
    return request.app.state.container.internal_api_secret


def get_agency_emails(request: Request) -> frozenset[str]:
    return request.app.state.container.agency_emails


def get_container(request: Request) -> Container:
    return request.app.state.container
