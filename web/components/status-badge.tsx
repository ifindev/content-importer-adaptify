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
  draft: "bg-muted text-muted-foreground",
  awaiting_approval:
    "bg-amber-100 text-amber-900 dark:bg-amber-900/40 dark:text-amber-200",
  changes_requested:
    "bg-orange-100 text-orange-900 dark:bg-orange-900/40 dark:text-orange-200",
  approved: "bg-blue-100 text-blue-900 dark:bg-blue-900/40 dark:text-blue-200",
  scheduled:
    "bg-violet-100 text-violet-900 dark:bg-violet-900/40 dark:text-violet-200",
  published:
    "bg-green-100 text-green-900 dark:bg-green-900/40 dark:text-green-200",
  failed: "bg-red-100 text-red-900 dark:bg-red-900/40 dark:text-red-200",
} as const;

export type Status = keyof typeof STATUS_LABEL;

export function StatusBadge({ status }: { status: Status }) {
  return (
    <Badge className={cn(STATUS_CLASS[status])}>{STATUS_LABEL[status]}</Badge>
  );
}
