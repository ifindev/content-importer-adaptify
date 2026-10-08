"use client";

import { Loader2, RefreshCw } from "lucide-react";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useTransition } from "react";

import { Button } from "@/components/ui/button";

const MIN_GAP_MS = 5_000;

/**
 * Re-fetches the page's server data when the tab comes back into focus, and
 * from a Refresh button. Changes made elsewhere (a client approving in their
 * own browser) only reach this page through a refetch. While it runs, the
 * current content stays and a dimmed "Checking for updates…" shows.
 *
 * `enabled={false}` turns both off, e.g. while there are unsaved edits a
 * refetch could discard.
 */
export function RefreshOnFocus({ enabled = true }: { enabled?: boolean }) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const last = useRef(0);

  const refresh = useCallback(() => {
    last.current = Date.now();
    startTransition(() => router.refresh());
  }, [router]);

  useEffect(() => {
    if (!enabled) return;
    function onFocus() {
      if (document.visibilityState !== "visible") return;
      if (Date.now() - last.current < MIN_GAP_MS) return;
      refresh();
    }
    window.addEventListener("focus", onFocus);
    document.addEventListener("visibilitychange", onFocus);
    return () => {
      window.removeEventListener("focus", onFocus);
      document.removeEventListener("visibilitychange", onFocus);
    };
  }, [enabled, refresh]);

  if (!enabled) return null;

  return (
    <div className="flex items-center gap-1.5">
      {pending && (
        <span
          role="status"
          className="text-faint flex items-center gap-1.5 text-[12.5px] max-md:sr-only"
        >
          <Loader2 className="size-3.5 animate-spin" />
          Checking for updates…
        </span>
      )}
      <Button
        variant="ghost"
        size="icon"
        aria-label="Refresh"
        title="Refresh"
        disabled={pending}
        onClick={refresh}
        className="text-faint hover:text-foreground max-md:size-11"
      >
        <RefreshCw className={pending ? "animate-spin" : undefined} />
      </Button>
    </div>
  );
}
