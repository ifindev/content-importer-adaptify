"use client";

import { CalendarDays, Loader2, RotateCw } from "lucide-react";
import { useTransition } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import type { Schemas } from "@/lib/api/types";
import { messageFor } from "@/lib/error-messages";
import { retryArticle } from "@/modules/articles/actions";

import { ScheduleDialog } from "./ScheduleDialog";

/**
 * The one inline action a row offers: Set date when Approved, Change date
 * when Scheduled (R4.5), Retry when Failed.
 */
export function RowAction({
  siteId,
  article,
}: {
  siteId: string;
  article: Schemas["ArticleSummary"];
}) {
  const [pending, startTransition] = useTransition();

  if (article.status === "approved") {
    return (
      <ScheduleDialog
        siteId={siteId}
        articleId={article.id}
        title={article.title}
        trigger={
          <Button
            variant="outline"
            size="sm"
            className="text-foreground/70 border-dashed border-[oklch(0.87_0.004_264)] bg-transparent shadow-none"
          >
            <CalendarDays /> Set date
          </Button>
        }
      />
    );
  }

  if (article.status === "scheduled") {
    return (
      <ScheduleDialog
        siteId={siteId}
        articleId={article.id}
        title={article.title}
        current={article.publish_at_utc}
        trigger={
          <Button variant="ghost" size="sm" className="text-foreground/70">
            <CalendarDays /> Change date
          </Button>
        }
      />
    );
  }

  if (article.status === "failed") {
    return (
      <Button
        variant="outline"
        size="sm"
        disabled={pending}
        onClick={() =>
          startTransition(async () => {
            const result = await retryArticle(siteId, article.id);
            if (result.ok) toast.success("Sent to WordPress again.");
            else toast.error(messageFor(result.code));
          })
        }
      >
        {pending ? <Loader2 className="animate-spin" /> : <RotateCw />}
        Retry
      </Button>
    );
  }

  return null;
}
