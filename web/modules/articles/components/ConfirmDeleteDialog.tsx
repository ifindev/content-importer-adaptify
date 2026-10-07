"use client";

import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogTitle,
} from "@/components/ui/dialog";

export function ConfirmDeleteDialog({
  open,
  onOpenChange,
  count,
  title,
  pending,
  onConfirm,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  count: number;
  title?: string;
  pending: boolean;
  onConfirm: () => void;
}) {
  const what = count === 1 ? "this article" : `${count} articles`;
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogTitle>Delete {what}?</DialogTitle>
        <DialogDescription>
          {title && count === 1 && (
            <>
              <span className="text-foreground font-medium">{title}</span> and
              its history will be removed.{" "}
            </>
          )}
          This can&apos;t be undone.
        </DialogDescription>
        <DialogFooter>
          <DialogClose render={<Button variant="ghost" />}>Cancel</DialogClose>
          <Button variant="destructive" onClick={onConfirm} disabled={pending}>
            {pending && <Loader2 className="animate-spin" />}
            Delete
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
