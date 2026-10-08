import uuid
from datetime import UTC, datetime

import pytest
from google.cloud import firestore

from app.adapters.firestore.repository import FirestoreArticleRepository
from app.adapters.firestore.site_repository import FirestoreSiteRepository
from app.adapters.testing.clock import FixedClock
from app.adapters.testing.scripted_publisher import ScriptedPublisher
from app.core.domain.models import Article, Event, Site
from app.core.domain.statuses import EventType, Status
from app.core.use_cases.build_report import build_report
from app.core.use_cases.sync_status import SyncCache

pytestmark = [pytest.mark.anyio, pytest.mark.integration]

FIRESTORE_EMULATOR_HOST = "localhost:8081"
PROJECT_ID = "demo-content-importer"
NOW = datetime(2026, 10, 7, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def site_id():
    return f"test-{uuid.uuid4()}"


@pytest.fixture
def repository(monkeypatch, site_id):
    monkeypatch.setenv("FIRESTORE_EMULATOR_HOST", FIRESTORE_EMULATOR_HOST)
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", PROJECT_ID)
    client = firestore.Client()
    yield FirestoreArticleRepository(client, site_id=site_id)
    # The emulator is shared with the dev stack; don't leave test sites behind.
    FirestoreSiteRepository(client).delete_site(site_id)


def _article(id_: str, status: Status, **overrides) -> Article:
    return Article(
        id=id_,
        title=f"Title {id_}",
        slug=id_,
        body_html="<p>hi</p>",
        source="paste",
        status=status,
        version=1,
        created_at=NOW,
        updated_at=NOW,
        **overrides,
    )


async def test_build_report_over_a_seeded_article_set(repository, site_id):
    repository.save_site(Site(id=site_id, name="My Site", wp_base_url="https://wp.example"))

    repository.create_article(_article("draft-1", Status.DRAFT))
    repository.create_article(_article("failed-1", Status.FAILED, last_error="WordPress 500"))
    published = repository.create_article(
        _article(
            "published-1",
            Status.PUBLISHED,
            published_url="https://wp.example/published-1",
        )
    )
    repository.save_article(
        published, Event(id="e1", type=EventType.PUBLISHED, actor="system", at=NOW)
    )

    report, unreachable = await build_report(
        repository, ScriptedPublisher(), FixedClock(NOW), SyncCache()
    )

    assert unreachable is False
    assert report.status_counts[Status.DRAFT] == 1
    assert report.status_counts[Status.FAILED] == 1
    assert report.status_counts[Status.PUBLISHED] == 1
    assert report.published_this_month == 1
    assert [e.article_id for e in report.published] == ["published-1"]
    assert {e.article_id for e in report.needs_attention} == {"failed-1"}
