from datetime import UTC, datetime

import pytest

from app.core.domain.errors import NotAllowed
from app.core.domain.lifecycle import ALLOWED_TRANSITIONS, transition
from app.core.domain.models import Article
from app.core.domain.statuses import EventType, Status

NOW = datetime(2026, 10, 7, 12, 0, 0, tzinfo=UTC)
LATER = datetime(2026, 10, 8, 9, 0, 0, tzinfo=UTC)

ALL_PAIRS = [(a, b) for a in Status for b in Status if a != b]


def _article(status: Status) -> Article:
    return Article(
        id="a1",
        title="Title",
        slug="title",
        body_html="<p>hi</p>",
        source="paste",
        status=status,
        version=1,
        created_at=NOW,
        updated_at=NOW,
    )


@pytest.mark.parametrize("from_status,to_status", ALL_PAIRS)
def test_every_transition_pair(from_status, to_status):
    article = _article(from_status)
    if to_status in ALLOWED_TRANSITIONS[from_status]:
        updated, event = transition(
            article, to_status, "agency", EventType.EDITED, LATER, data=None
        )
        assert updated.status == to_status
        assert updated.updated_at == LATER
        assert event.type == EventType.EDITED
        assert event.at == LATER
    else:
        with pytest.raises(NotAllowed):
            transition(article, to_status, "agency", EventType.EDITED, LATER)


def test_published_is_terminal():
    assert ALLOWED_TRANSITIONS[Status.PUBLISHED] == set()


def test_event_data_is_attached():
    article = _article(Status.AWAITING_APPROVAL)
    _, event = transition(
        article,
        Status.CHANGES_REQUESTED,
        "client",
        EventType.CHANGES_REQUESTED,
        LATER,
        data={"comment": "fix the title"},
    )
    assert event.data == {"comment": "fix the title"}
