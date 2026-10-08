"use client";

import { Loader2 } from "lucide-react";
import { useState, useTransition } from "react";
import { toast } from "sonner";

import { DateTimePicker } from "@/components/date-time-picker";
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
import { Label } from "@/components/ui/label";
import { messageFor } from "@/lib/error-messages";
import { scheduleArticle } from "@/modules/articles/actions";

/** The API refuses a publish time closer than this (or in the past). */
const MIN_LEAD_MS = 5 * 60_000;

/** The picker works in local wall time without a zone: "YYYY-MM-DDTHH:mm". */
function formatLocal(d: Date) {
  const shifted = new Date(d.getTime() - d.getTimezoneOffset() * 60_000);
  return shifted.toISOString().slice(0, 16);
}

function toLocalInput(iso: string | null | undefined) {
  return formatLocal(iso ? new Date(iso) : new Date(Date.now() + 864e5));
}

/** Earliest allowed value: now + 5 minutes, rounded up to a whole minute
 *  because the picker has no seconds. Same-format strings compare as text. */
function earliestLocal() {
  const d = new Date(Date.now() + MIN_LEAD_MS);
  if (d.getSeconds() > 0 || d.getMilliseconds() > 0) {
    d.setSeconds(0, 0);
    d.setMinutes(d.getMinutes() + 1);
  }
  return formatLocal(d);
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
  const [value, setValue] = useState("");
  const [min, setMin] = useState("");

  // Recomputed on every open, so the limit follows the clock.
  function handleOpenChange(next: boolean) {
    if (next) {
      const earliest = earliestLocal();
      const wanted = toLocalInput(current);
      // A stored date that has passed (Failed) isn't a useful default.
      setValue(current && wanted >= earliest ? wanted : toLocalInput(null));
      setMin(earliest);
      setError(null);
    }
    setOpen(next);
  }

  const tooSoon = value !== "" && value < min;
  const shownError = tooSoon ? "publish_at_in_past" : error;

  function submit(formData: FormData) {
    const local = String(formData.get("publish_at") ?? "");
    // Time has passed since the dialog opened: check against now, not `min`.
    if (local < earliestLocal()) {
      setError("publish_at_in_past");
      return;
    }
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
    <Dialog open={open} onOpenChange={handleOpenChange}>
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
          <DateTimePicker
            id="publish_at"
            name="publish_at"
            value={value}
            min={min}
            onChange={(next) => {
              setValue(next);
              setError(null);
            }}
            invalid={!!shownError}
          />
          {shownError && (
            <p role="alert" className="text-destructive text-[12.5px]">
              {messageFor(shownError)}
            </p>
          )}
          <DialogFooter className="mt-3">
            <DialogClose render={<Button variant="ghost" />}>
              Cancel
            </DialogClose>
            <Button type="submit" disabled={pending || tooSoon}>
              {pending && <Loader2 className="animate-spin" />}
              Schedule
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
