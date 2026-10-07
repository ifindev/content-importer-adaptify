import type { Status } from "@/components/status-badge";

/** Spec: Approval rules. Only articles that never reached WordPress. */
export const isDeletable = (status: Status) =>
  status === "draft" || status === "changes_requested";
