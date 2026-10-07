import { ChevronRight, ExternalLink } from "lucide-react";
import Link from "next/link";

import { LocalTime } from "@/components/local-time";
import { PageHeader } from "@/components/page-header";
import { StatusBadge, type Status } from "@/components/status-badge";
import { SyncWarningBadge } from "@/components/sync-warning-badge";
import { WordPressBanner } from "@/components/wordpress-banner";
import { cn } from "@/lib/utils";
import { getReport } from "@/modules/report/data";

const STATUSES: Status[] = [
  "draft",
  "awaiting_approval",
  "changes_requested",
  "approved",
  "scheduled",
  "published",
  "failed",
];

const CARD = "rounded-xl border bg-card shadow-[0_1px_2px_oklch(0_0_0/0.03)]";
const ROW =
  "flex min-h-[46px] items-center gap-2.5 border-t border-[oklch(0.955_0.003_264)] px-3.5 text-[13.5px] first:border-t-0";

export async function ReportPage({ siteId }: { siteId: string }) {
  const report = await getReport(siteId);
  const total = Object.values(report.status_counts).reduce((a, b) => a + b, 0);
  const rounds = report.change_rounds.reduce((sum, r) => sum + r.rounds, 0);
  const article = (id: string) => `/sites/${siteId}/articles/${id}`;
  const month = new Date().toLocaleDateString("en-US", {
    month: "long",
    year: "numeric",
  });

  return (
    <>
      <PageHeader title="Report" subtitle={month} />
      <div className="flex flex-col gap-5 px-4 pt-4 pb-8 md:px-7 md:pt-5">
        {report.wordpress_unreachable && <WordPressBanner />}

        <section aria-label="Key metrics" className="grid gap-3 sm:grid-cols-3">
          <Kpi
            label="Published this month"
            value={String(report.published_this_month)}
            note={`${report.status_counts.published ?? 0} published in total`}
          />
          <Kpi
            label="Time to approval"
            value={
              report.avg_approval_seconds == null
                ? "—"
                : (report.avg_approval_seconds / 86400).toFixed(1)
            }
            unit={report.avg_approval_seconds == null ? undefined : "days"}
            note="Average, from first sent to approved"
          />
          <Kpi
            label="Change rounds"
            value={total ? (rounds / total).toFixed(1) : "—"}
            unit={total ? "per article" : undefined}
            note="Average client change requests"
          />
        </section>

        <section className={cn(CARD, "px-5 pt-4 pb-2")}>
          <div className="mb-2 flex items-baseline justify-between">
            <h2 className="text-sm font-semibold">Articles by status</h2>
            <span className="text-muted-foreground text-[12.5px]">
              {total} total
            </span>
          </div>
          <div className="grid gap-x-10 sm:[grid-auto-flow:column] sm:grid-cols-2 sm:grid-rows-4">
            {STATUSES.map((status) => (
              <Link
                key={status}
                href={`/sites/${siteId}/articles?status=${status}`}
                className="hover:bg-muted/40 focus-visible:ring-ring/50 flex h-[46px] items-center gap-2.5 border-t border-[oklch(0.955_0.003_264)] pr-1.5 outline-none focus-visible:ring-3"
              >
                <StatusBadge status={status} />
                <span className="ml-auto text-sm font-medium tabular-nums">
                  {report.status_counts[status] ?? 0}
                </span>
                <ChevronRight className="text-faint size-4" />
              </Link>
            ))}
          </div>
        </section>

        <div className="grid gap-5 lg:grid-cols-2">
          <List
            title="Needs attention"
            count={report.needs_attention.length}
            empty="Nothing needs attention."
          >
            {report.needs_attention.map((n) => (
              <Link
                key={n.article_id + n.reason}
                href={article(n.article_id)}
                className={cn(ROW, "hover:bg-muted/40")}
              >
                {n.reason === "failed" ? (
                  <StatusBadge status="failed" />
                ) : (
                  <SyncWarningBadge warning={n.reason} />
                )}
                <span className="min-w-0 flex-1 truncate">{n.title}</span>
                {n.detail && (
                  <span className="text-muted-foreground max-w-[40%] truncate text-[12.5px]">
                    {n.detail}
                  </span>
                )}
              </Link>
            ))}
          </List>

          <List
            title="Upcoming"
            count={report.upcoming.length}
            empty="Nothing scheduled."
          >
            {report.upcoming.map((u) => (
              <Link
                key={u.article_id}
                href={article(u.article_id)}
                className={cn(ROW, "hover:bg-muted/40")}
              >
                <span className="min-w-0 flex-1 truncate">{u.title}</span>
                <span className="text-muted-foreground shrink-0 text-[12.5px]">
                  <LocalTime iso={u.publish_at_utc} format="short" />
                </span>
              </Link>
            ))}
          </List>

          <List
            title="Change rounds"
            count={report.change_rounds.length}
            empty="No change requests yet."
          >
            {report.change_rounds.map((c) => (
              <Link
                key={c.article_id}
                href={article(c.article_id)}
                className={cn(ROW, "hover:bg-muted/40")}
              >
                <span className="min-w-0 flex-1 truncate">{c.title}</span>
                <span className="text-muted-foreground shrink-0 text-[12.5px] tabular-nums">
                  {c.rounds} {c.rounds === 1 ? "round" : "rounds"}
                </span>
              </Link>
            ))}
          </List>

          <List
            title="Published"
            count={report.published.length}
            empty="Nothing published yet."
            wide
          >
            {report.published.map((p) => (
              <div
                key={p.article_id}
                className={cn(ROW, "max-sm:flex-wrap max-sm:py-2")}
              >
                <Link
                  href={article(p.article_id)}
                  className="min-w-0 flex-1 truncate hover:underline"
                >
                  {p.title}
                </Link>
                <span className="text-muted-foreground w-[90px] shrink-0 text-[12.5px]">
                  <LocalTime iso={p.published_at} format="short" />
                </span>
                <a
                  href={p.published_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-foreground/65 hover:text-foreground inline-flex min-w-0 items-center gap-1 text-[12.5px] hover:underline max-sm:basis-full"
                >
                  <span className="truncate">
                    {p.published_url.replace(/^https?:\/\//, "")}
                  </span>
                  <ExternalLink className="size-3 shrink-0" />
                </a>
              </div>
            ))}
          </List>
        </div>
      </div>
    </>
  );
}

function Kpi({
  label,
  value,
  unit,
  note,
}: {
  label: string;
  value: string;
  unit?: string;
  note: string;
}) {
  return (
    <div className={cn(CARD, "px-5 py-[18px]")}>
      <div className="text-foreground/65 text-[13px] font-medium">{label}</div>
      <div className="mt-2.5 text-[28px] leading-tight font-semibold tracking-tight tabular-nums">
        {value}
        {unit && (
          <span className="text-muted-foreground ml-1.5 text-sm font-medium tracking-normal">
            {unit}
          </span>
        )}
      </div>
      <div className="text-muted-foreground mt-1.5 text-[12.5px]">{note}</div>
    </div>
  );
}

function List({
  title,
  count,
  empty,
  wide,
  children,
}: {
  title: string;
  count: number;
  empty: string;
  wide?: boolean;
  children: React.ReactNode;
}) {
  return (
    <section className={cn("min-w-0", wide && "lg:col-span-2")}>
      <div className="mb-2.5 flex items-baseline gap-2">
        <h2 className="text-sm font-semibold">{title}</h2>
        <span className="text-muted-foreground text-[12.5px]">{count}</span>
      </div>
      <div className={CARD}>
        {count === 0 ? (
          <p className="text-muted-foreground px-3.5 py-3.5 text-[13px]">
            {empty}
          </p>
        ) : (
          children
        )}
      </div>
    </section>
  );
}
