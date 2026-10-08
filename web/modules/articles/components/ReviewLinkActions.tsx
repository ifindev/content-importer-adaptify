"use client";

import { ChevronDown, Link2, Loader2, RotateCcw } from "lucide-react";
import { useState, useTransition } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { messageFor } from "@/lib/error-messages";
import { resetReviewLink } from "@/modules/articles/actions";

async function copy(url: string) {
  try {
    await navigator.clipboard.writeText(url);
    return true;
  } catch {
    return false;
  }
}

/** Copy the site's review link, or reset it so the old one stops working (R3.7). */
export function ReviewLinkActions({
  siteId,
  url,
}: {
  siteId: string;
  url: string;
}) {
  const [resetOpen, setResetOpen] = useState(false);
  const [pending, startTransition] = useTransition();

  async function copyCurrent() {
    if (await copy(url)) toast.success("Review link copied.");
    else toast.error("Couldn't copy. The link is " + url);
  }

  function reset() {
    startTransition(async () => {
      const result = await resetReviewLink(siteId);
      if (!result.ok) {
        toast.error(messageFor(result.code));
        return;
      }
      setResetOpen(false);
      toast.success(
        (await copy(result.data.url))
          ? "Review link reset. The new link is copied."
          : "Review link reset.",
      );
    });
  }

  return (
    <div className="flex">
      <Button
        variant="outline"
        onClick={copyCurrent}
        aria-label="Copy review link"
        className="max-md:size-11 max-md:border-0 max-md:shadow-none md:rounded-r-none"
      >
        <Link2 />
        <span className="max-md:hidden">Copy review link</span>
      </Button>
      <DropdownMenu>
        <DropdownMenuTrigger
          render={
            <Button
              variant="outline"
              size="icon"
              aria-label="Review link options"
              title="Review link options"
              className="max-md:size-11 max-md:border-0 max-md:shadow-none md:-ml-px md:rounded-l-none"
            />
          }
        >
          <ChevronDown />
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-48">
          <DropdownMenuItem
            variant="destructive"
            onClick={() => setResetOpen(true)}
          >
            <RotateCcw /> Reset review link
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <Dialog open={resetOpen} onOpenChange={setResetOpen}>
        <DialogContent className="text-left">
          <DialogTitle>Reset the review link?</DialogTitle>
          <DialogDescription>
            The current link stops working at once. Send the new link to your
            client.
          </DialogDescription>
          <DialogFooter className="mt-3">
            <DialogClose render={<Button variant="ghost" />}>
              Cancel
            </DialogClose>
            <Button variant="destructive" onClick={reset} disabled={pending}>
              {pending && <Loader2 className="animate-spin" />}
              Reset link
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
