"use client";

import {
  Copy,
  ExternalLink,
  FileText,
  MoreHorizontal,
  Trash2,
} from "lucide-react";
import Link from "next/link";
import { useState, useTransition } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { Schemas } from "@/lib/api/types";
import { messageFor } from "@/lib/error-messages";
import { deleteArticle } from "@/modules/articles/actions";

import { ConfirmDeleteDialog } from "./ConfirmDeleteDialog";
import { isDeletable } from "./deletable";

/**
 * A row's "More actions". Set date, Change date and Retry stay inline
 * (RowAction); this holds the rest.
 */
export function RowMenu({
  siteId,
  article,
}: {
  siteId: string;
  article: Schemas["ArticleSummary"];
}) {
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [pending, startTransition] = useTransition();
  const live = article.published_url;

  async function copyLive() {
    try {
      await navigator.clipboard.writeText(live!);
      toast.success("Live link copied.");
    } catch {
      toast.error("Couldn't copy. The link is " + live);
    }
  }

  function remove() {
    startTransition(async () => {
      const result = await deleteArticle(siteId, article.id);
      if (!result.ok) {
        toast.error(messageFor(result.code));
        return;
      }
      setConfirmOpen(false);
      toast.success("Draft deleted.");
    });
  }

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger
          render={
            <Button
              variant="ghost"
              size="icon-sm"
              aria-label={`More actions for ${article.title}`}
              title="More actions"
            />
          }
        >
          <MoreHorizontal />
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-44">
          <DropdownMenuItem
            render={<Link href={`/sites/${siteId}/articles/${article.id}`} />}
          >
            <FileText /> Open
          </DropdownMenuItem>
          {live && (
            <>
              <DropdownMenuItem
                render={
                  <a href={live} target="_blank" rel="noopener noreferrer" />
                }
              >
                <ExternalLink /> View live
              </DropdownMenuItem>
              <DropdownMenuItem onClick={copyLive}>
                <Copy /> Copy live link
              </DropdownMenuItem>
            </>
          )}
          {isDeletable(article.status) && (
            <DropdownMenuItem
              variant="destructive"
              onClick={() => setConfirmOpen(true)}
            >
              <Trash2 /> Delete
            </DropdownMenuItem>
          )}
        </DropdownMenuContent>
      </DropdownMenu>
      <ConfirmDeleteDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        count={1}
        title={article.title}
        pending={pending}
        onConfirm={remove}
      />
    </>
  );
}
