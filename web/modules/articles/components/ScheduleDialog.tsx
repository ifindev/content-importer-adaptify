"use client";

import { Loader2 } from "lucide-react";
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
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { messageFor } from "@/lib/error-messages";
import { scheduleArticle } from "@/modules/articles/actions";

/** `datetime-local` wants local wall time without a zone. */
function toLocalInput(iso: string | null | undefined) {
  const d = iso ? new Date(iso) : new Date(Date.now() + 864e5);
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
  return d.toISOString().slice(0, 16);
}

export function ScheduleDialog({
  siteId,
  articleId,
  title,
  current,
  trigger,
}: {
  siteId: string;
  articleId: string;
  title: string;
  current?: string | null;
  trigger: React.ReactElement;
}) {
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  function submit(formData: FormData) {
    const local = String(formData.get("publish_at") ?? "");
    setError(null);
    startTransition(async () => {
      const result = await scheduleArticle(
        siteId,
        articleId,
        new Date(local).toISOString(),
      );
      if (!result.ok) {
        setError(result.code);
        return;
      }
      toast.success("Scheduled in WordPress.");
      setOpen(false);
    });
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger render={trigger} />
      <DialogContent className="sm:max-w-[400px]">
        <DialogTitle>
          {current ? "Change publish date" : "Set publish date"}
        </DialogTitle>
        <DialogDescription className="truncate">{title}</DialogDescription>
        <form
          // onSubmit, not action: React resets a form after its action runs,
          // which would drop the picked date when the API says it's past.
          onSubmit={(e) => {
            e.preventDefault();
            submit(new FormData(e.currentTarget));
          }}
          className="flex flex-col gap-1.5"
        >
          <Label htmlFor="publish_at">Publish at (your time)</Label>
          <Input
            id="publish_at"
            name="publish_at"
            type="datetime-local"
            defaultValue={toLocalInput(current)}
            required
            aria-invalid={error ? true : undefined}
          />
          {error && (
            <p role="alert" className="text-destructive text-[12.5px]">
              {messageFor(error)}
            </p>
          )}
          <DialogFooter className="mt-3">
            <DialogClose render={<Button variant="ghost" />}>
              Cancel
            </DialogClose>
            <Button type="submit" disabled={pending}>
              {pending && <Loader2 className="animate-spin" />}
              Schedule
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
