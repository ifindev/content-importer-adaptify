import { TriangleAlert } from "lucide-react";

export function WordPressBanner() {
  return (
    <div
      role="alert"
      className="flex items-center gap-2.5 rounded-[9px] border border-[oklch(0.91_0.045_27.325)] bg-[oklch(0.97_0.015_27.325)] px-3 py-2.5 text-[13px] text-[oklch(0.42_0.17_27.325)]"
    >
      <TriangleAlert className="size-4 shrink-0" />
      Can&apos;t reach WordPress. Statuses may be out of date.
    </div>
  );
}
