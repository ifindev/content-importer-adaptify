import type { Status } from "@/components/status-badge";

export const STATUS_OPTIONS: (Status | "needs_attention")[] = [
  "draft",
  "awaiting_approval",
  "changes_requested",
  "approved",
  "scheduled",
  "published",
  "failed",
  "needs_attention",
];
