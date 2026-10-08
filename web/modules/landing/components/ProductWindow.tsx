import { StatusBadge } from "@/components/status-badge";
import { SAMPLE_ROWS, type SampleRow } from "@/modules/landing/content";

function RowStatus({ row }: { row: SampleRow }) {
  if (!row.flips) return <StatusBadge status={row.status} />;
  return (
    <span className="grid justify-items-start [&>*]:col-start-1 [&>*]:row-start-1">
      <span className="flip-a">
        <StatusBadge status={row.status} />
      </span>
      <span className="flip-b">
        <StatusBadge status="approved" />
      </span>
    </span>
  );
}

const SITE_DOT = <span className="bg-status-published size-5 rounded-md" />;

/** The articles screen as a decorative mock: a browser window on desktop, a phone below md. */
export function ProductWindow() {
  return (
    <section
      aria-label="The articles screen"
      className="mx-auto max-w-[1180px] px-3 md:px-12"
    >
      <div
        className="halftone reveal rounded-[20px] px-5 pt-9 md:px-[72px] md:pt-[72px]"
        aria-hidden
      >
        {/* Desktop: browser window */}
        <div className="hidden overflow-hidden rounded-t-[14px] shadow-[0_12px_32px_-8px_oklch(0.2_0.1_264/0.35),0_2px_6px_oklch(0_0_0/0.06)] md:block">
          <div className="bg-app grid h-[460px] grid-cols-[210px_1fr]">
            <aside className="border-r px-3 py-[18px] text-[13px] font-medium">
              <div className="flex items-center gap-2 px-2 py-1.5">
                {SITE_DOT}Kestrel Running
              </div>
              <div className="text-muted-foreground mt-3.5 flex flex-col gap-0.5">
                <span className="bg-background text-foreground rounded-[7px] px-2.5 py-[7px] shadow-[0_0_0_1px_var(--border)]">
                  Articles
                </span>
                <span className="px-2.5 py-[7px]">Import</span>
                <span className="px-2.5 py-[7px]">Report</span>
              </div>
            </aside>
            <div className="px-6 pt-6">
              <div className="mb-4 flex items-center justify-between">
                <span className="text-[19px] font-semibold tracking-tight">
                  Articles
                </span>
                <span className="bg-primary text-primary-foreground rounded-lg px-3 py-1.5 text-[13px] font-medium">
                  Import
                </span>
              </div>
              <div className="bg-background overflow-hidden rounded-xl border">
                <div className="text-muted-foreground grid h-[38px] grid-cols-[1fr_170px_140px] items-center px-[18px] text-xs">
                  <span>Title</span>
                  <span>Status</span>
                  <span>Publish date</span>
                </div>
                {SAMPLE_ROWS.map((row) => (
                  <div
                    key={row.title}
                    className="grid h-[54px] grid-cols-[1fr_170px_140px] items-center border-t border-[oklch(0.955_0.003_264)] px-[18px] text-[13px]"
                  >
                    <span className="text-[13.5px] font-medium">
                      {row.title}
                    </span>
                    <RowStatus row={row} />
                    <span className={row.date ? "tabular-nums" : "text-faint"}>
                      {row.date ?? "—"}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
        {/* Mobile: phone */}
        <div className="bg-background mx-auto max-w-[300px] overflow-hidden rounded-t-[28px] border-[6px] border-b-0 border-[oklch(0.15_0_0)] md:hidden">
          <div className="flex h-12 items-center justify-between border-b px-3.5">
            <span className="text-[15px] font-semibold">Articles</span>
            <span className="bg-primary text-primary-foreground rounded-md px-2.5 py-1 text-[12.5px] font-medium">
              Import
            </span>
          </div>
          {SAMPLE_ROWS.slice(0, 5).map((row) => (
            <div
              key={row.title}
              className="border-b border-[oklch(0.955_0.003_264)] px-3.5 py-[11px] last:border-b-0"
            >
              <p className="text-[13.5px] font-medium">{row.title}</p>
              <div className="mt-1.5">
                <RowStatus row={row} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
