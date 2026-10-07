import { Badge } from "@/components/ui/badge";

const SYNC_WARNING_LABEL = {
  late: "Late",
  changed_in_wordpress: "Changed in WordPress",
  missing_in_wordpress: "Missing in WordPress",
} as const;

export type SyncWarning = keyof typeof SYNC_WARNING_LABEL;

export function SyncWarningBadge({ warning }: { warning: SyncWarning }) {
  return (
    <Badge className="bg-status-failed text-status-failed-fg h-5 px-[7px] text-[11.5px]">
      {SYNC_WARNING_LABEL[warning]}
    </Badge>
  );
}
