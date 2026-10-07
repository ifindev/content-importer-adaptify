from dataclasses import asdict

from fastapi import APIRouter, Depends, Request

from app.api.auth import require_session
from app.api.schemas.report import (
    ChangeRoundsEntry,
    NeedsAttentionEntry,
    PublishedEntry,
    ReportOut,
    UpcomingEntry,
)
from app.api.tags import REPORT
from app.core.ports.article_repository import ArticleRepository
from app.core.ports.clock import Clock
from app.core.ports.publisher import Publisher
from app.core.use_cases.build_report import build_report
from app.core.use_cases.sync_status import SyncCache

router = APIRouter(dependencies=[Depends(require_session)])


def get_repository(request: Request) -> ArticleRepository:
    return request.app.state.container.article_repository


def get_clock(request: Request) -> Clock:
    return request.app.state.container.clock


def get_publisher(request: Request) -> Publisher:
    return request.app.state.container.publisher


def get_sync_cache(request: Request) -> SyncCache:
    return request.app.state.container.sync_cache


@router.get("/report", tags=[REPORT])
async def get_report(
    repository: ArticleRepository = Depends(get_repository),
    publisher: Publisher = Depends(get_publisher),
    clock: Clock = Depends(get_clock),
    cache: SyncCache = Depends(get_sync_cache),
) -> ReportOut:
    report, unreachable = await build_report(repository, publisher, clock, cache)
    return ReportOut(
        status_counts=report.status_counts,
        published_this_month=report.published_this_month,
        avg_approval_seconds=report.avg_approval_seconds,
        change_rounds=[ChangeRoundsEntry(**asdict(c)) for c in report.change_rounds],
        upcoming=[UpcomingEntry(**asdict(c)) for c in report.upcoming],
        published=[PublishedEntry(**asdict(c)) for c in report.published],
        needs_attention=[NeedsAttentionEntry(**asdict(c)) for c in report.needs_attention],
        wordpress_unreachable=unreachable,
    )
