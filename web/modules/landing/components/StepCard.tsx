import { cn } from "@/lib/utils";

const FLOAT =
  "bg-background rounded-[14px] shadow-[0_12px_32px_-8px_oklch(0.2_0.1_264/0.35),0_2px_6px_oklch(0_0_0/0.06)]";
const FILE_ROW =
  "flex items-center justify-between rounded-[10px] border px-3.5 py-[11px] text-[13px]";

export const PANEL_TINT = [
  "",
  "halftone-violet",
  "halftone-orange",
  "halftone-green",
] as const;

function ImportCard() {
  return (
    <div className={cn(FLOAT, "w-full max-w-[400px] p-5")}>
      <p className="text-[15px] font-semibold">Import</p>
      <div className="bg-muted mt-3 inline-flex gap-0.5 rounded-lg p-[3px] text-[12.5px] font-medium">
        <span className="text-muted-foreground px-2.5 py-1">Paste</span>
        <span className="bg-background rounded-md px-2.5 py-1 shadow-xs">
          Upload
        </span>
      </div>
      <div className="text-muted-foreground mt-3 rounded-[10px] border border-dashed border-[oklch(0.85_0.01_264)] p-[18px] text-center text-[13px]">
        Drop .docx files here
      </div>
      <div className="mt-2.5 flex flex-col gap-1.5">
        {["recovery-runs.docx", "carb-loading.docx", "trail-shoes.docx"].map(
          (f) => (
            <div key={f} className={FILE_ROW}>
              <span className="font-mono text-[12.5px]">{f}</span>
              <span className="text-muted-foreground text-[12.5px]">
                Draft created
              </span>
            </div>
          ),
        )}
      </div>
    </div>
  );
}

function ReviewCard() {
  return (
    <div className={cn(FLOAT, "w-full max-w-[400px] p-[22px]")}>
      <p className="text-faint text-xs">Kestrel Running · Review</p>
      <p className="display mt-1.5 text-[21px] leading-tight">
        10 marathon training mistakes
      </p>
      <p className="mt-3 text-[13.5px] leading-[1.7] text-[oklch(0.35_0_0)]">
        Most first marathons go wrong weeks before race day. Here are the ten
        mistakes we see most often.
      </p>
      <div className="bg-muted mt-3 h-2 w-[90%] rounded" />
      <div className="mt-5 flex gap-2">
        <span className="flex h-9 flex-1 items-center justify-center rounded-lg border text-[13px] font-medium">
          Request changes
        </span>
        <span className="bg-primary text-primary-foreground flex h-9 flex-1 items-center justify-center rounded-lg text-[13px] font-medium">
          Approve
        </span>
      </div>
    </div>
  );
}

function ScheduleCard() {
  const field = (label: string, value: string) => (
    <div className="flex-1">
      <p className="text-[12.5px] font-medium">{label}</p>
      <p className="mt-1.5 flex h-9 items-center rounded-lg border px-3 text-[13.5px] tabular-nums">
        {value}
      </p>
    </div>
  );
  return (
    <div className={cn(FLOAT, "w-full max-w-[400px] p-[22px]")}>
      <p className="text-[15px] font-semibold">Schedule article</p>
      <p className="text-muted-foreground mt-0.5 text-[13px]">
        10 marathon training mistakes
      </p>
      <div className="mt-4 flex gap-2.5">
        {field("Date", "Tue, Oct 14, 2026")}
        {field("Time", "09:00")}
      </div>
      <div className="bg-app mt-3.5 flex justify-between rounded-[10px] px-3.5 py-3 text-[13px]">
        <span className="text-muted-foreground">Publishes on</span>
        <span className="font-mono text-[12.5px]">kestrelrunning.com</span>
      </div>
      <span className="bg-foreground text-background mt-4 flex h-[38px] items-center justify-center rounded-lg text-[13.5px] font-medium">
        Schedule
      </span>
    </div>
  );
}

const REPORT = [
  ["Published this month", "14"],
  ["Avg. time to approval", "1.8 days"],
  ["Change rounds per article", "1.2"],
  ["Needs attention", "1"],
] as const;

function ReportCard() {
  return (
    <div className="grid w-full max-w-[440px] grid-cols-2 gap-2.5">
      {REPORT.map(([label, value]) => (
        <div key={label} className={cn(FLOAT, "px-4 py-4 md:px-5")}>
          <p className="text-muted-foreground text-[12.5px] md:text-[13px]">
            {label}:
          </p>
          <p className="mt-1.5 font-mono text-[20px] tracking-tight md:text-2xl">
            {value}
          </p>
        </div>
      ))}
    </div>
  );
}

/** The floating UI shown on each step's panel. Decorative. */
export function StepCard({ step }: { step: number }) {
  return [
    <ImportCard key={0} />,
    <ReviewCard key={1} />,
    <ScheduleCard key={2} />,
    <ReportCard key={3} />,
  ][step];
}
