"use client";

import { Loader2, MoreHorizontal, Pencil, Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";
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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { messageFor } from "@/lib/error-messages";
import { deleteSite } from "@/modules/sites/actions";

export function SiteRowActions({
  site,
}: {
  site: { id: string; name: string; article_count: number };
}) {
  const router = useRouter();
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [typed, setTyped] = useState("");
  const [pending, startTransition] = useTransition();

  function remove() {
    startTransition(async () => {
      const result = await deleteSite(site.id);
      if (!result.ok) {
        toast.error(messageFor(result.code));
        return;
      }
      setDeleteOpen(false);
      toast.success(`${site.name} deleted.`);
      router.refresh();
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
              aria-label={`More actions for ${site.name}`}
            />
          }
        >
          <MoreHorizontal />
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-40">
          <DropdownMenuItem
            // Client-only URL update opens the dialog without a round trip.
            onClick={() =>
              window.history.pushState(null, "", `/sites?edit=${site.id}`)
            }
          >
            <Pencil /> Edit
          </DropdownMenuItem>
          <DropdownMenuItem
            variant="destructive"
            onClick={() => {
              setTyped("");
              setDeleteOpen(true);
            }}
          >
            <Trash2 /> Delete
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <DialogContent className="text-left">
          <DialogTitle>Delete {site.name}?</DialogTitle>
          <DialogDescription>
            This removes the site, its {site.article_count}{" "}
            {site.article_count === 1 ? "article" : "articles"} with their
            history, and its review link. Posts already in WordPress stay as
            they are. This can&apos;t be undone.
          </DialogDescription>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (typed === site.name) remove();
            }}
            className="flex flex-col gap-1.5"
          >
            <Label htmlFor={`confirm-${site.id}`}>
              Type <span className="font-semibold">{site.name}</span> to confirm
            </Label>
            <Input
              id={`confirm-${site.id}`}
              value={typed}
              onChange={(e) => setTyped(e.target.value)}
              autoComplete="off"
            />
            <DialogFooter className="mt-3">
              <DialogClose render={<Button variant="ghost" />}>
                Cancel
              </DialogClose>
              <Button
                type="submit"
                variant="destructive"
                disabled={typed !== site.name || pending}
              >
                {pending && <Loader2 className="animate-spin" />}
                Delete site
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
}
