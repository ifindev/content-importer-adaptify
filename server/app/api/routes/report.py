from dataclasses import asdict

from fastapi import APIRouter, Depends

from app.api.auth import require_session
from app.api.deps import SiteContext, get_clock, get_site_context, get_sync_cache
from app.api.schemas.report import (
    ChangeRoundsEntry,
    NeedsAttentionEntry,
    PublishedEntry,
    ReportOut,
    UpcomingEntry,
)
from app.api.tags import REPORT
from app.core.ports.clock import Clock
from app.core.use_cases.build_report import build_report
from app.core.use_cases.sync_status import SyncCache

router = APIRouter(dependencies=[Depends(require_session)])


@router.get("/report", tags=[REPORT])
async def get_report(
    ctx: SiteContext = Depends(get_site_context),
    clock: Clock = Depends(get_clock),
    cache: SyncCache = Depends(get_sync_cache),
) -> ReportOut:
    report, unreachable = await build_report(
        ctx.repository, ctx.publisher, clock, cache, site_id=ctx.site_id
    )
    return ReportOut(
        status_counts=report.status_counts,
        published_this_month=report.published_this_month,
        avg_approval_seconds=report.avg_approval_seconds,
        avg_change_rounds=report.avg_change_rounds,
        change_rounds=[ChangeRoundsEntry(**asdict(c)) for c in report.change_rounds],
        upcoming=[UpcomingEntry(**asdict(c)) for c in report.upcoming],
        published=[PublishedEntry(**asdict(c)) for c in report.published],
        needs_attention=[NeedsAttentionEntry(**asdict(c)) for c in report.needs_attention],
        wordpress_unreachable=unreachable,
    )
