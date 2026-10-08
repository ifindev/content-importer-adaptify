"use client";

import {
  Check,
  CircleAlert,
  ExternalLink,
  Loader2,
  MessageSquare,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState, useTransition } from "react";
import { toast } from "sonner";

import { LocalTime } from "@/components/local-time";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { Schemas } from "@/lib/api/types";
import { messageFor } from "@/lib/error-messages";
import { approve, requestChanges } from "@/modules/review/actions";

const NAME_KEY = "review_client_name";

function readName() {
  try {
    return localStorage.getItem(NAME_KEY) ?? "";
  } catch {
    return "";
  }
}

function rememberName(name: string) {
  try {
    localStorage.setItem(NAME_KEY, name);
  } catch {
    // Private mode or blocked storage: the field just won't be prefilled.
  }
}

export function DecisionPanel({
  token,
  article,
  card,
}: {
  token: string;
  article: Schemas["ReviewArticleOut"];
  card: Schemas["ArticleCard"] | undefined;
}) {
  const router = useRouter();
  const [name, setName] = useState("");
  const [comment, setComment] = useState("");
  const [mode, setMode] = useState<"decide" | "changes">("decide");
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();
  const [pendingAction, setPendingAction] = useState<
    "approve" | "changes" | null
  >(null);

  // localStorage only exists in the browser, so read it after hydration.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => setName(readName()), []);

  if (article.status !== "awaiting_approval") {
    return <ReadOnlyPanel article={article} card={card} />;
  }

  function decide(kind: "approve" | "changes") {
    if (!name.trim()) {
      setError("name_required");
      return;
    }
    if (kind === "changes" && !comment.trim()) {
      setError("comment_required");
      return;
    }
    setError(null);
    rememberName(name.trim());
    setPendingAction(kind);
    startTransition(async () => {
      const result =
        kind === "approve"
          ? await approve(token, article.id, {
              client_name: name.trim(),
              version: article.version,
            })
          : await requestChanges(token, article.id, {
              client_name: name.trim(),
              comment: comment.trim(),
              version: article.version,
            });
      setPendingAction(null);
      if (!result.ok) {
        setError(result.code);
        return;
      }
      toast.success(
        kind === "approve" ? "Approved. Thank you!" : "Sent to the agency.",
      );
      // The article leaves the client's view once decided (spec: Client
      // view), so reloading this reader would 404. Back to the list.
      router.push(`/review/${token}`);
    });
  }

  const errorText =
    error === "name_required"
      ? "Add your name so the agency knows who decided."
      : error === "comment_required"
        ? "Say what should change."
        : error && messageFor(error);

  const errorBox = errorText && (
    <div
      role="alert"
      className="flex flex-col gap-2 rounded-[9px] border border-[oklch(0.91_0.045_27.325)] bg-[oklch(0.97_0.015_27.325)] px-3 py-2.5 text-[13px] text-[oklch(0.42_0.17_27.325)]"
    >
      <span className="flex gap-2">
        <CircleAlert className="mt-px size-4 shrink-0" />
        {errorText}
      </span>
      {(error === "article_changed" || error === "not_awaiting_approval") && (
        <Button
          variant="outline"
          size="sm"
          className="self-start"
          onClick={() => router.refresh()}
        >
          Reload
        </Button>
      )}
    </div>
  );

  const nameField = (id: string) => (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={id}>Your name</Label>
      <Input
        id={id}
        autoComplete="name"
        placeholder="So the agency knows who decided"
        value={name}
        onChange={(e) => setName(e.target.value)}
        aria-invalid={error === "name_required" || undefined}
        className="max-lg:h-10 max-lg:text-[15px]"
      />
      <span className="text-muted-foreground text-xs">
        Remembered on this device
      </span>
    </div>
  );

  const commentField = (id: string, rows: number) => (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={id}>What should change?</Label>
      <Textarea
        id={id}
        rows={rows}
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        aria-invalid={error === "comment_required" || undefined}
        className="resize-y max-lg:text-[15px]"
      />
      <span className="text-muted-foreground text-xs">
        Be specific: mention the section or sentence.
      </span>
    </div>
  );

  const spin = (kind: "approve" | "changes") =>
    pending && pendingAction === kind ? (
      <Loader2 className="animate-spin" />
    ) : null;

  return (
    <>
      {/* lg+: side panel */}
      <aside
        aria-label="Your decision"
        className="hidden w-[320px] shrink-0 border-l p-6 lg:block"
      >
        <div className="sticky top-6 flex flex-col gap-4">
          {mode === "decide" ? (
            <>
              <div>
                <h2 className="text-[15px] font-semibold">Your decision</h2>
                <p className="text-muted-foreground mt-1 text-[13px] leading-normal">
                  Approve it to go ahead, or tell the agency what to change.
                </p>
              </div>
              {errorBox}
              {nameField("name-panel")}
              <div className="flex flex-col gap-2">
                <Button
                  onClick={() => decide("approve")}
                  disabled={pending}
                  className="w-full"
                >
                  {spin("approve") ?? <Check />} Approve
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setError(null);
                    setMode("changes");
                  }}
                  disabled={pending}
                  className="w-full"
                >
                  <MessageSquare /> Request changes
                </Button>
              </div>
            </>
          ) : (
            <>
              <div>
                <h2 className="text-[15px] font-semibold">Request changes</h2>
                <p className="text-muted-foreground mt-1 text-[13px] leading-normal">
                  The agency sees this note on the article and sends it back for
                  your approval.
                </p>
              </div>
              {errorBox}
              {commentField("comment-panel", 7)}
              {nameField("name-panel")}
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => setMode("decide")}
                >
                  Cancel
                </Button>
                <Button
                  className="flex-1"
                  onClick={() => decide("changes")}
                  disabled={pending}
                >
                  {spin("changes")} Send request
                </Button>
              </div>
            </>
          )}
        </div>
      </aside>

      {/* Below lg: a sticky bottom bar. Request changes grows it into the
          form over a light blur; the article stays readable above it. */}
      {mode === "changes" && (
        // A light veil to set the form apart; it doesn't catch touches, so
        // the article above still scrolls and stays readable.
        <div
          aria-hidden
          className="bg-foreground/5 pointer-events-none fixed inset-0 z-10 backdrop-blur-[1.5px] lg:hidden"
        />
      )}
      <section
        aria-label={mode === "changes" ? "Request changes" : "Your decision"}
        onKeyDown={(e) => e.key === "Escape" && setMode("decide")}
        className="bg-background sticky bottom-0 z-20 flex max-h-[70svh] flex-col gap-3 overflow-y-auto border-t px-4 pt-3 pb-4 lg:hidden"
      >
        {mode === "changes" ? (
          <>
            <div>
              <h2 className="text-[15px] font-semibold">Request changes</h2>
              <p className="text-muted-foreground mt-0.5 text-[13px]">
                The agency sees this note on the article and sends it back for
                your approval.
              </p>
            </div>
            {errorBox}
            {commentField("comment-bar", 3)}
            {nameField("name-bar")}
            <div className="flex gap-2">
              <Button
                variant="outline"
                className="h-10 flex-1"
                onClick={() => setMode("decide")}
              >
                Cancel
              </Button>
              <Button
                className="h-10 flex-1"
                onClick={() => decide("changes")}
                disabled={pending}
              >
                {spin("changes")} Send request
              </Button>
            </div>
          </>
        ) : (
          <>
            {errorBox}
            {nameField("name-bar")}
            <div className="flex gap-2">
              <Button
                variant="outline"
                className="h-10 flex-1"
                onClick={() => {
                  setError(null);
                  setMode("changes");
                }}
                disabled={pending}
              >
                Request changes
              </Button>
              <Button
                className="h-10 flex-1"
                onClick={() => decide("approve")}
                disabled={pending}
              >
                {spin("approve")} Approve
              </Button>
            </div>
          </>
        )}
      </section>
    </>
  );
}

function ReadOnlyPanel({
  article,
  card,
}: {
  article: Schemas["ReviewArticleOut"];
  card: Schemas["ArticleCard"] | undefined;
}) {
  // The client only sees Scheduled and Published once they've decided.
  const published = article.status === "published";

  return (
    <aside
      aria-label="Status"
      className="border-t px-5 py-4 lg:w-[320px] lg:shrink-0 lg:border-t-0 lg:border-l lg:p-6"
    >
      <div className="flex flex-col gap-2 text-[13.5px] lg:sticky lg:top-6">
        <h2 className="text-[15px] font-semibold">
          {published ? "Published" : "Scheduled"}
        </h2>
        {published && (
          <p className="text-muted-foreground">This article is live.</p>
        )}
        {!published && card?.publish_at_utc && (
          <p className="text-muted-foreground">
            Publishes <LocalTime iso={card.publish_at_utc} format="datetime" />.
          </p>
        )}
        {card?.published_url && (
          <a
            href={card.published_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-foreground/70 hover:text-foreground inline-flex items-center gap-1.5 hover:underline"
          >
            View the live page <ExternalLink className="size-3.5" />
          </a>
        )}
      </div>
    </aside>
  );
}
