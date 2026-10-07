import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const STATUS_LABEL = {
  draft: "Draft",
  awaiting_approval: "Awaiting approval",
  changes_requested: "Changes requested",
  approved: "Approved",
  scheduled: "Scheduled",
  published: "Published",
  failed: "Failed",
} as const;

const STATUS_CLASS = {
  draft: "bg-status-draft text-status-draft-fg",
  awaiting_approval: "bg-status-awaiting text-status-awaiting-fg",
  changes_requested: "bg-status-changes text-status-changes-fg",
  approved: "bg-status-approved text-status-approved-fg",
  scheduled: "bg-status-scheduled text-status-scheduled-fg",
  published: "bg-status-published text-status-published-fg",
  failed: "bg-status-failed text-status-failed-fg",
} as const;

export type Status = keyof typeof STATUS_LABEL;

export function statusLabel(status: Status) {
  return STATUS_LABEL[status];
}

export function StatusBadge({ status }: { status: Status }) {
  return (
    <Badge className={cn("h-[22px] px-2", STATUS_CLASS[status])}>
      {STATUS_LABEL[status]}
    </Badge>
  );
}
