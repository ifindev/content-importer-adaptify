import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

const DIVIDER = "border-[oklch(0.955_0.003_264)]";

function Cell({
  title,
  text,
  children,
  className,
}: {
  title: string;
  text: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "lift reveal bg-background flex flex-col justify-between gap-7 rounded-2xl border p-6 md:p-8",
        className,
      )}
    >
      <div aria-hidden>{children}</div>
      <div>
        <h3 className="display text-xl tracking-[-0.015em] md:text-[21px]">
          {title}
        </h3>
        <p className="text-muted-foreground mt-1.5 max-w-[420px] text-[14.5px] leading-relaxed">
          {text}
        </p>
      </div>
    </div>
  );
}

const Dot = ({ color }: { color: string }) => (
  <span
    className="size-[7px] shrink-0 rounded-full"
    style={{ background: color }}
  />
);

export function Bento() {
  return (
    <section
      id="features"
      className="mx-auto max-w-[1180px] scroll-mt-20 px-5 pt-22 md:px-12 md:pt-32"
    >
      <h2 className="display reveal max-w-[640px] text-[32px] leading-[1.12] md:text-[44px] md:leading-[1.1]">
        Everything around the article, handled
      </h2>
      <div className="mt-8 grid gap-3 md:mt-14 md:grid-cols-2 md:gap-4 lg:grid-cols-3">
        <Cell
          className="bg-app lg:col-span-2"
          title="Import from anywhere"
          text="Paste from Google Docs, Word or the web, or drop in several .docx files. Headings, lists and links survive; messy styling doesn't."
        >
          <div className="grid gap-4 sm:grid-cols-[1.3fr_1fr]">
            <div className="bg-background hidden rounded-xl border p-[18px] sm:block">
              <p className="text-faint font-mono text-[11.5px]">
                Pasted from Google Docs
              </p>
              <p className="mt-2.5 text-base font-semibold">
                Hill repeats for flat-landers
              </p>
              <p className="mt-2 text-[13px] leading-relaxed text-[oklch(0.35_0_0)]">
                No hills nearby? Bridges, ramps and a treadmill get you most of
                the way.
              </p>
              <ul className="mt-2.5 list-disc pl-4 text-[13px] leading-[1.8] text-[oklch(0.35_0_0)]">
                <li>6 × 60s uphill, easy jog down</li>
                <li>Keep the effort, not the pace</li>
              </ul>
            </div>
            <div className="flex flex-col gap-2">
              {[
                "recovery-runs.docx",
                "carb-loading.docx",
                "trail-shoes.docx",
              ].map((f) => (
                <div
                  key={f}
                  className="bg-background flex justify-between rounded-[10px] border px-3.5 py-3 font-mono text-[12.5px]"
                >
                  {f}
                  <span className="text-faint">Draft</span>
                </div>
              ))}
            </div>
          </div>
        </Cell>

        <div className="halftone lift reveal flex min-h-[420px] flex-col justify-between gap-7 rounded-2xl p-6 md:p-8 lg:row-span-2">
          <div
            aria-hidden
            className="bg-background mx-auto w-[220px] overflow-hidden rounded-[28px] border-[6px] border-[oklch(0.15_0_0)]"
          >
            <div className="border-b px-3.5 pt-3.5 pb-2.5">
              <p className="text-faint text-[10.5px]">Waiting for you</p>
              <p className="text-sm font-semibold">2 articles</p>
            </div>
            <p
              className={cn(
                "border-b px-3.5 py-3 text-[12.5px] font-medium",
                DIVIDER,
              )}
            >
              10 marathon training mistakes
            </p>
            <p
              className={cn(
                "border-b px-3.5 py-3 text-[12.5px] font-medium",
                DIVIDER,
              )}
            >
              How to pick a running shoe
            </p>
            <p className="text-faint px-3.5 pt-3 text-[10.5px]">Upcoming</p>
            <p className="text-muted-foreground px-3.5 pt-1.5 pb-4 text-[12.5px]">
              Recovery runs, explained
            </p>
          </div>
          <div className="halftone-scrim" />
          <div className="text-white">
            <h3 className="display text-xl tracking-[-0.015em] md:text-[21px]">
              One link per client
            </h3>
            <p className="mt-1.5 text-[14.5px] leading-relaxed text-white/85">
              No account, no password. It doubles as your client&apos;s content
              report.
            </p>
          </div>
        </div>

        <Cell
          title="Approval reset"
          text="Edit after approval and it goes back to the client. What goes live is what they said yes to."
        >
          <div className="seq font-mono text-[12.5px]">
            {[
              ["#10b981", "09:12", "Approved by Dana"],
              ["var(--foreground)", "10:40", "Edited by you"],
              ["oklch(0.8 0 0)", "10:40", "Back to draft"],
            ].map(([color, time, label]) => (
              <div key={label} className="flex items-center gap-3 py-2.5">
                <Dot color={color} />
                <span className="text-faint">{time}</span>
                {label}
              </div>
            ))}
          </div>
        </Cell>

        <Cell
          title="In sync with WordPress"
          text="If someone edits a post straight in WordPress, you'll know."
        >
          <div className="text-[13.5px]">
            {[
              ["#f59e0b", "Late"],
              ["#f59e0b", "Changed in WordPress"],
              ["#ef4444", "Missing in WordPress"],
            ].map(([color, label], i) => (
              <div
                key={label}
                className={cn(
                  "flex items-center gap-2.5 py-[9px]",
                  i < 2 && "border-b",
                  DIVIDER,
                )}
              >
                <Dot color={color} />
                {label}
              </div>
            ))}
          </div>
        </Cell>

        <Cell
          className="md:col-span-2"
          title="Reporting that writes itself"
          text="Every live URL, how fast clients approve, and what needs your attention."
        >
          <div className="grid grid-cols-3">
            {[
              ["14", "Published this month"],
              ["1.8d", "Avg. time to approval"],
              ["1.2", "Change rounds"],
            ].map(([value, label], i) => (
              <div key={label} className={cn(i > 0 && "border-l pl-4 md:pl-7")}>
                <p className="font-mono text-[28px] tracking-tight md:text-[40px]">
                  {value}
                </p>
                <p className="text-muted-foreground text-[12.5px] md:text-[13.5px]">
                  {label}
                </p>
              </div>
            ))}
          </div>
          <p className="text-faint mt-3 text-xs">Example report</p>
        </Cell>

        <Cell
          className="bg-app"
          title="Every client site"
          text="One dashboard, with connections tested and passwords encrypted."
        >
          <div className="text-[13.5px] font-medium">
            {["kestrelrunning.com", "northbakery.co", "harbordental.com"].map(
              (site, i) => (
                <div
                  key={site}
                  className={cn(
                    "flex items-center justify-between py-[9px]",
                    i < 2 && "border-b",
                  )}
                >
                  {site}
                  <Dot color="#10b981" />
                </div>
              ),
            )}
          </div>
        </Cell>
      </div>
    </section>
  );
}
