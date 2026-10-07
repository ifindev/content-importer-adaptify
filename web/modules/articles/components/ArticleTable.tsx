"use client";

import { Trash2 } from "lucide-react";
import Link from "next/link";
import { useState, useTransition } from "react";
import { toast } from "sonner";

import { LocalTime } from "@/components/local-time";
import { StatusBadge } from "@/components/status-badge";
import { SyncWarningBadge } from "@/components/sync-warning-badge";
import { Button } from "@/components/ui/button";
import type { Schemas } from "@/lib/api/types";
import { messageFor } from "@/lib/error-messages";
import { deleteArticle } from "@/modules/articles/actions";

import { ConfirmDeleteDialog } from "./ConfirmDeleteDialog";
import { isDeletable } from "./deletable";
import { RowAction } from "./RowAction";

const CHECKBOX = "accent-primary size-4 cursor-pointer align-middle";

export function ArticleTable({
  siteId,
  articles,
}: {
  siteId: string;
  articles: Schemas["ArticleSummary"][];
}) {
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [pending, startTransition] = useTransition();

  const deletable = articles.filter((a) => isDeletable(a.status));
  // Rows can leave the list (filter change, deleted elsewhere): drop stale ids.
  const chosen = deletable.filter((a) => selected.has(a.id));
  const allChosen = deletable.length > 0 && chosen.length === deletable.length;

  function toggle(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (!next.delete(id)) next.add(id);
      return next;
    });
  }

  function deleteChosen() {
    startTransition(async () => {
      // No bulk endpoint (T-034): one call per article, failures reported.
      const failed: string[] = [];
      for (const a of chosen) {
        const result = await deleteArticle(siteId, a.id);
        if (!result.ok) failed.push(`${a.title}: ${messageFor(result.code)}`);
      }
      const deleted = chosen.length - failed.length;
      if (deleted)
        toast.success(
          `Deleted ${deleted} ${deleted === 1 ? "article" : "articles"}.`,
        );
      if (failed.length) toast.error(failed.join("\n"));
      setSelected(new Set());
      setConfirmOpen(false);
    });
  }

  return (
    <div className="md:px-4 md:pb-5">
      {chosen.length > 0 && (
        <div
          role="status"
          className="bg-background sticky top-2 z-10 mx-4 mb-2 flex items-center gap-3 rounded-lg border px-3 py-2 text-[13px] md:mx-0"
        >
          <span className="font-medium">{chosen.length} selected</span>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSelected(new Set())}
          >
            Clear
          </Button>
          <Button
            variant="destructive"
            size="sm"
            className="ml-auto"
            onClick={() => setConfirmOpen(true)}
          >
            <Trash2 /> Delete
          </Button>
        </div>
      )}
      <table className="w-full border-collapse text-[13px]">
        <thead className="max-md:sr-only">
          <tr className="text-muted-foreground border-b text-left text-xs">
            <th className="h-9 w-10 pl-3">
              {deletable.length > 0 && (
                <input
                  type="checkbox"
                  aria-label="Select all deletable articles"
                  className={CHECKBOX}
                  checked={allChosen}
                  onChange={() =>
                    setSelected(
                      allChosen
                        ? new Set()
                        : new Set(deletable.map((a) => a.id)),
                    )
                  }
                />
              )}
            </th>
            <th className="h-9 px-3 font-medium">Title</th>
            <th className="h-9 w-[170px] px-3 font-medium">Status</th>
            <th className="h-9 w-[150px] px-3 font-medium">Publish date</th>
            <th className="h-9 w-[110px] px-3">
              <span className="sr-only">Actions</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {articles.map((a) => (
            <tr
              key={a.id}
              className="hover:bg-muted/40 border-b border-[oklch(0.955_0.003_264)] max-md:flex max-md:flex-wrap max-md:items-center max-md:gap-x-2 max-md:gap-y-1.5 max-md:px-4 max-md:py-3.5"
            >
              <td className="pl-3 max-md:order-last max-md:p-0 max-md:empty:hidden">
                {isDeletable(a.status) && (
                  <input
                    type="checkbox"
                    aria-label={`Select ${a.title}`}
                    className={CHECKBOX}
                    checked={selected.has(a.id)}
                    onChange={() => toggle(a.id)}
                  />
                )}
              </td>
              <td className="px-3 py-2 max-md:w-full max-md:p-0 md:h-[52px]">
                <Link
                  href={`/sites/${siteId}/articles/${a.id}`}
                  className="focus-visible:ring-ring/50 rounded-sm text-[14.5px] font-medium outline-none hover:underline focus-visible:ring-3 md:text-[13.5px]"
                >
                  {a.title}
                </Link>
                {a.sync_warning && (
                  <span className="ml-2 max-md:hidden">
                    <SyncWarningBadge warning={a.sync_warning} />
                  </span>
                )}
              </td>
              <td className="px-3 py-2 max-md:p-0">
                <StatusBadge status={a.status} />
              </td>
              {a.sync_warning && (
                <td className="p-0 md:hidden">
                  <SyncWarningBadge warning={a.sync_warning} />
                </td>
              )}
              <td className="text-foreground/75 px-3 py-2 max-md:p-0 max-md:text-[12.5px] max-md:empty:hidden">
                {a.publish_at_utc ? (
                  <LocalTime iso={a.publish_at_utc} />
                ) : (
                  <span className="text-faint max-md:hidden">—</span>
                )}
              </td>
              <td className="px-3 py-2 text-right max-md:ml-auto max-md:p-0 max-md:empty:hidden">
                <RowAction siteId={siteId} article={a} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <ConfirmDeleteDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        count={chosen.length}
        title={chosen[0]?.title}
        pending={pending}
        onConfirm={deleteChosen}
      />
    </div>
  );
}
