"use client";

import {
  ArrowLeft,
  CalendarDays,
  CalendarX2,
  ChevronDown,
  ExternalLink,
  Loader2,
  RotateCw,
  Trash2,
  TriangleAlert,
  Undo2,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState, useTransition } from "react";
import { toast } from "sonner";

import { ArticleEditor } from "@/components/article-editor";
import { LocalTime } from "@/components/local-time";
import { RefreshOnFocus } from "@/components/refresh-on-focus";
import { StatusBadge } from "@/components/status-badge";
import { SyncWarningBadge } from "@/components/sync-warning-badge";
import { Button, buttonVariants } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogTitle,
} from "@/components/ui/dialog";
import type { Schemas } from "@/lib/api/types";
import { messageFor } from "@/lib/error-messages";
import type { MutationResult } from "@/lib/mutation-result";
import { cn } from "@/lib/utils";
import {
  deleteArticle,
  pullBack,
  retryArticle,
  sendForReview,
  unscheduleArticle,
  updateArticle,
} from "@/modules/articles/actions";

import { ConfirmDeleteDialog } from "./ConfirmDeleteDialog";
import { isDeletable } from "./deletable";
import { ScheduleDialog } from "./ScheduleDialog";

type Article = Schemas["ArticleDetail"];

const EDITABLE = new Set<Article["status"]>(["draft", "changes_requested"]);
// Scheduled is read-only (like Awaiting approval): unschedule it first.
const RESETS_APPROVAL = new Set<Article["status"]>(["approved"]);

const EVENT_TEXT: Record<Schemas["EventType"], string> = {
  imported: "imported the article",
  edited: "edited",
  sent_for_review: "sent for review",
  pulled_back: "pulled back to Draft",
  approved: "approved",
  changes_requested: "requested changes",
  scheduled: "scheduled",
  date_changed: "changed the publish date",
  unscheduled: "took it off the schedule",
  published: "published",
  failed: "publish failed",
  retried: "retried",
  ai_draft_created: "drafted a change",
  ai_draft_accepted: "accepted the drafted change",
};

/**
 * Who an event is shown as. Agency events store the session's Firebase uid,
 * which means nothing to a reader; the one shared agency login (R8.1) makes
 * "Agency" exact. Client decisions carry the name the client typed.
 */
function actorLabel(event: Schemas["EventOut"]) {
  if (event.type === "approved" || event.type === "changes_requested")
    return event.actor;
  if (event.type === "published" || event.type === "failed") return "WordPress";
  return "Agency";
}

export function ArticleDetail({
  siteId,
  siteHost,
  article,
}: {
  siteId: string;
  siteHost: string;
  article: Article;
}) {
  const [title, setTitle] = useState(article.title);
  const [slug, setSlug] = useState(article.slug);
  const [body, setBody] = useState(article.body_html);
  const [unlocked, setUnlocked] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  // "Edit anyway" unmounts the Edit button the dialog would return focus to;
  // land in the title instead, ready to type.
  const titleRef = useRef<HTMLTextAreaElement>(null);
  const focusTitleOnClose = useRef(false);
  const [pending, startTransition] = useTransition();
  const [pendingAction, setPendingAction] = useState<string | null>(null);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const router = useRouter();

  function remove() {
    setPendingAction("delete");
    startTransition(async () => {
      const result = await deleteArticle(siteId, article.id);
      setPendingAction(null);
      if (!result.ok) {
        toast.error(messageFor(result.code));
        setDeleteOpen(false);
        return;
      }
      toast.success("Article deleted.");
      router.push(`/sites/${siteId}/articles`);
    });
  }

  const deleteButton = isDeletable(article.status) && (
    <Button
      variant="ghost"
      aria-label="Delete article"
      title="Delete article"
      onClick={() => setDeleteOpen(true)}
      disabled={pending}
      className="text-destructive hover:text-destructive"
    >
      <Trash2 />
      <span className="max-lg:sr-only">Delete</span>
    </Button>
  );

  const editable = EDITABLE.has(article.status) || unlocked;
  const dirty =
    title !== article.title ||
    slug !== article.slug ||
    body !== article.body_html;

  useEffect(() => {
    if (!dirty) return;
    const warn = (e: BeforeUnloadEvent) => e.preventDefault();
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);

  function run(
    name: string,
    action: () => Promise<MutationResult<unknown>>,
    done?: string,
  ) {
    setPendingAction(name);
    startTransition(async () => {
      const result = await action();
      setPendingAction(null);
      if (!result.ok) toast.error(messageFor(result.code));
      else if (done) toast.success(done);
    });
  }

  function save() {
    run("save", () =>
      updateArticle(siteId, article.id, {
        title: title !== article.title ? title : null,
        slug: slug !== article.slug ? slug : null,
        body_html: body !== article.body_html ? body : null,
      }),
    );
  }

  function send() {
    run(
      "send",
      async () => {
        if (dirty) {
          const saved = await updateArticle(siteId, article.id, {
            title,
            slug,
            body_html: body,
          });
          if (!saved.ok) return saved;
        }
        return sendForReview(siteId, article.id);
      },
      "Sent to the client for review.",
    );
  }

  const busy = (name: string) => pending && pendingAction === name;
  const spinner = (name: string) =>
    busy(name) ? <Loader2 className="animate-spin" /> : null;

  const primary = (() => {
    switch (article.status) {
      case "draft":
      case "changes_requested":
        return (
          <Button onClick={send} disabled={pending}>
            {spinner("send")}
            {article.status === "draft" ? "Send for review" : "Resubmit"}
          </Button>
        );
      case "awaiting_approval":
        return (
          <Button
            onClick={() =>
              run(
                "pull",
                () => pullBack(siteId, article.id),
                "Pulled back to Draft.",
              )
            }
            disabled={pending}
          >
            {spinner("pull") ?? <Undo2 />}
            Pull back
          </Button>
        );
      case "approved":
        return unlocked ? null : (
          <ScheduleDialog
            siteId={siteId}
            articleId={article.id}
            title={article.title}
            trigger={
              <Button>
                <CalendarDays /> Set date
              </Button>
            }
          />
        );
      case "scheduled":
        return (
          <>
            <Button
              variant="outline"
              onClick={() =>
                run(
                  "unschedule",
                  () => unscheduleArticle(siteId, article.id),
                  "Taken off the schedule.",
                )
              }
              disabled={pending}
            >
              {spinner("unschedule") ?? <CalendarX2 />}
              Unschedule
            </Button>
            <ScheduleDialog
              siteId={siteId}
              articleId={article.id}
              title={article.title}
              current={article.publish_at_utc}
              trigger={
                <Button>
                  <CalendarDays /> Change date
                </Button>
              }
            />
          </>
        );
      case "failed":
        return (
          <>
            {/* A new date, for when the one Retry would reuse has passed. */}
            <ScheduleDialog
              siteId={siteId}
              articleId={article.id}
              title={article.title}
              current={article.publish_at_utc}
              trigger={
                <Button variant="outline">
                  <CalendarDays /> Set date
                </Button>
              }
            />
            <Button
              onClick={() =>
                run(
                  "retry",
                  () => retryArticle(siteId, article.id),
                  "Sent to WordPress again.",
                )
              }
              disabled={pending}
            >
              {spinner("retry") ?? <RotateCw />}
              Retry
            </Button>
          </>
        );
      case "published":
        return article.published_url ? (
          <a
            href={article.published_url}
            target="_blank"
            rel="noopener noreferrer"
            className={buttonVariants()}
          >
            <ExternalLink /> View live
          </a>
        ) : null;
    }
  })();

  const saveState = busy("save")
    ? "Saving…"
    : dirty
      ? "Unsaved changes"
      : editable
        ? "Saved"
        : null;

  const saveButton = editable && (
    <Button variant="outline" onClick={save} disabled={!dirty || pending}>
      {spinner("save")}
      Save
    </Button>
  );

  return (
    <div className="flex min-h-svh flex-col md:h-[calc(100svh-1rem)] md:min-h-0">
      {/* Top bar. On mobile the window scrolls, so it sticks there. */}
      <div className="bg-background flex h-[52px] shrink-0 items-center gap-3 border-b px-1 max-md:sticky max-md:top-0 max-md:z-20 md:px-3.5 md:pl-5">
        <Link
          href={`/sites/${siteId}/articles`}
          aria-label="Back to articles"
          className={cn(
            buttonVariants({ variant: "ghost", size: "icon" }),
            "size-11 md:hidden",
          )}
        >
          <ArrowLeft />
        </Link>
        <nav
          aria-label="Breadcrumb"
          className="flex min-w-0 flex-1 items-center gap-1.5 text-[13px]"
        >
          <Link
            href={`/sites/${siteId}/articles`}
            className="text-muted-foreground hover:text-foreground rounded-sm"
          >
            Articles
          </Link>
          <span className="text-faint max-md:hidden">/</span>
          <span
            aria-current="page"
            className="truncate font-medium max-md:hidden"
          >
            {article.title}
          </span>
          <span className="ml-1.5 shrink-0">
            <StatusBadge status={article.status} />
          </span>
        </nav>
        {saveState && (
          <span
            role="status"
            className="text-faint text-[12.5px] max-md:hidden"
          >
            {saveState}
          </span>
        )}
        {/* Not while editing: a refetch that brings a new version remounts
            the editor and would drop unsaved text. */}
        <RefreshOnFocus enabled={!dirty} />
        <div className="flex items-center gap-2 max-md:hidden">
          {dirty && saveButton}
          {RESETS_APPROVAL.has(article.status) && !unlocked && (
            <Button variant="outline" onClick={() => setConfirmOpen(true)}>
              Edit
            </Button>
          )}
          {deleteButton}
          {primary}
        </div>
      </div>

      <div className="flex min-h-0 flex-1 max-md:flex-col">
        {/* Editor column. It scrolls on its own only from md: on mobile an
            overflow here would trap the toolbar's sticky inside it. */}
        <div className="min-w-0 flex-1 md:overflow-y-auto">
          <StatusNotice article={article} unlocked={unlocked} />
          <ArticleEditor
            content={article.body_html}
            editable={editable}
            onChange={setBody}
            toolbarClassName="max-md:top-[52px]"
            header={
              <>
                <textarea
                  ref={titleRef}
                  aria-label="Title"
                  rows={1}
                  value={title}
                  onChange={(e) => setTitle(e.target.value.replace(/\n/g, " "))}
                  readOnly={!editable}
                  className="[field-sizing:content] w-full resize-none bg-transparent text-2xl leading-tight font-semibold tracking-tight outline-none md:text-[28px]"
                />
                <div className="text-muted-foreground mt-1.5 mb-6 flex min-w-0 items-center text-[13px]">
                  <span className="shrink-0">{siteHost}/</span>
                  <input
                    aria-label="Slug"
                    value={slug}
                    onChange={(e) => setSlug(e.target.value)}
                    readOnly={!editable}
                    className="focus-visible:bg-muted min-w-0 flex-1 rounded-sm bg-transparent outline-none"
                  />
                </div>
                <div className="md:hidden">
                  <Feedback article={article} />
                </div>
              </>
            }
          />
        </div>

        {/* Side panel */}
        <aside className="shrink-0 overflow-y-auto border-l p-5 max-md:border-t max-md:border-l-0 max-md:px-4 md:w-80">
          <div className="max-md:hidden">
            <Feedback article={article} />
          </div>
          <SidePanel article={article} />
        </aside>
      </div>

      {/* Mobile action bar */}
      <div className="bg-background sticky bottom-0 flex items-center justify-end gap-2 border-t px-4 py-3 md:hidden">
        {saveState && (
          <span role="status" className="text-faint mr-auto text-[12.5px]">
            {saveState}
          </span>
        )}
        {saveButton}
        {RESETS_APPROVAL.has(article.status) && !unlocked && (
          <Button variant="outline" onClick={() => setConfirmOpen(true)}>
            Edit
          </Button>
        )}
        {deleteButton}
        {primary}
      </div>

      <ConfirmDeleteDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        count={1}
        title={article.title}
        pending={pending && pendingAction === "delete"}
        onConfirm={remove}
      />
      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent
          finalFocus={() =>
            focusTitleOnClose.current ? titleRef.current : true
          }
        >
          <DialogTitle>Edit this article?</DialogTitle>
          <DialogDescription>
            Editing resets the client&apos;s approval. Saving moves the article
            back to Draft, and the client has to approve it again.
          </DialogDescription>
          <DialogFooter>
            <DialogClose render={<Button variant="ghost" />}>
              Cancel
            </DialogClose>
            <Button
              onClick={() => {
                focusTitleOnClose.current = true;
                setUnlocked(true);
                setConfirmOpen(false);
              }}
            >
              Edit anyway
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function StatusNotice({
  article,
  unlocked,
}: {
  article: Article;
  unlocked: boolean;
}) {
  const notice =
    article.status === "failed"
      ? {
          tone: "error",
          text: article.last_error ?? "The WordPress call failed.",
        }
      : article.status === "awaiting_approval"
        ? {
            tone: "info",
            text: "Waiting for the client. Pull it back to edit.",
          }
        : article.status === "scheduled"
          ? {
              tone: "info",
              text: "Scheduled in WordPress. Unschedule it to edit.",
            }
          : unlocked
            ? {
                tone: "warn",
                text: "Edit the article, then Save. Saving moves it back to Draft and resets the client's approval.",
              }
            : null;
  if (!notice) return null;
  return (
    <div
      role={notice.tone === "error" ? "alert" : "status"}
      className={cn(
        "flex items-center gap-2 border-b px-5 py-2.5 text-[13px]",
        notice.tone === "error" && "bg-status-failed text-status-failed-fg",
        notice.tone === "warn" && "bg-status-changes text-status-changes-fg",
        notice.tone === "info" && "bg-status-awaiting text-status-awaiting-fg",
      )}
    >
      {notice.tone !== "info" && <TriangleAlert className="size-4 shrink-0" />}
      {notice.text}
    </div>
  );
}

function Feedback({ article }: { article: Article }) {
  if (!article.client_comment) return null;
  const request = article.events.findLast(
    (e) => e.type === "changes_requested",
  );
  return (
    <section className="mb-6">
      <h2 className="mb-2.5 text-[13px] font-semibold">Client feedback</h2>
      <div className="rounded-[10px] border border-[oklch(0.93_0.035_85)] bg-[oklch(0.985_0.012_85)] p-3.5">
        {request && (
          <div className="mb-2 flex items-center gap-2 text-[13px]">
            <span className="flex size-[22px] items-center justify-center rounded-full bg-[oklch(0.93_0.05_80)] text-[11px] font-semibold text-[oklch(0.45_0.1_60)] uppercase">
              {request.actor.charAt(0)}
            </span>
            <span className="font-medium">{request.actor}</span>
            <span className="text-muted-foreground text-xs">
              <LocalTime iso={request.at} format="short" />
            </span>
          </div>
        )}
        <p className="text-foreground/85 text-[13.5px] leading-normal whitespace-pre-line">
          {article.client_comment}
        </p>
      </div>
    </section>
  );
}

function SidePanel({ article }: { article: Article }) {
  return (
    <div className="flex flex-col gap-6">
      {(article.sync_warning ||
        article.published_url ||
        article.publish_at_utc) && (
        <section className="flex flex-col gap-2 text-[13px]">
          <h2 className="text-[13px] font-semibold">WordPress</h2>
          {article.sync_warning && (
            <SyncWarningBadge warning={article.sync_warning} />
          )}
          {article.publish_at_utc && (
            <span className="text-foreground/75">
              {article.status === "published" ? "Published " : "Publishes "}
              <LocalTime iso={article.publish_at_utc} format="datetime" />
            </span>
          )}
          {article.published_url && (
            <a
              href={article.published_url}
              target="_blank"
              rel="noreferrer"
              className="text-foreground/70 hover:text-foreground inline-flex min-w-0 items-center gap-1.5 hover:underline"
            >
              <span className="truncate">
                {article.published_url.replace(/^https?:\/\//, "")}
              </span>
              <ExternalLink className="size-3 shrink-0" />
            </a>
          )}
        </section>
      )}
      {article.warnings.length > 0 && (
        <section>
          <h2 className="mb-2 text-[13px] font-semibold">Import warnings</h2>
          <ul className="text-status-changes-fg flex flex-col gap-1.5 text-[13px]">
            {article.warnings.map((w) => (
              <li key={w} className="flex gap-2">
                <TriangleAlert className="mt-0.5 size-3.5 shrink-0" />
                {w}
              </li>
            ))}
          </ul>
        </section>
      )}
      <section>
        <h2 className="mb-3.5 text-[13px] font-semibold">Activity</h2>
        <ol>
          {[...article.events].reverse().map((event, i, all) => (
            <li
              key={event.id}
              className="relative flex gap-3 pb-[18px] last:pb-0"
            >
              {i < all.length - 1 && (
                <span
                  aria-hidden
                  className="bg-border absolute top-4 bottom-0 left-1 w-px"
                />
              )}
              <span
                aria-hidden
                className={cn(
                  "bg-background mt-1.5 size-[9px] shrink-0 rounded-full border-2 border-[oklch(0.8_0_0)]",
                  event.type === "changes_requested" && "border-amber-600",
                  event.type === "approved" && "border-emerald-600",
                  event.type === "failed" && "border-red-600",
                )}
              />
              <ActivityEntry event={event} />
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}

/** A change request's comment opens under its line, collapsed by default. */
function ActivityEntry({ event }: { event: Schemas["EventOut"] }) {
  const line = (
    <>
      <div className="text-[13px]">
        <span className="font-medium">{actorLabel(event)}</span>{" "}
        {EVENT_TEXT[event.type]}
      </div>
      <div className="text-muted-foreground text-xs">
        <LocalTime iso={event.at} format="datetime" />
      </div>
    </>
  );
  const comment =
    event.type === "changes_requested" ? event.data?.comment : undefined;
  if (typeof comment !== "string" || !comment) {
    return <div>{line}</div>;
  }
  return (
    <details className="group min-w-0 flex-1">
      <summary className="focus-visible:ring-ring/50 cursor-pointer list-none rounded-sm outline-none focus-visible:ring-3 [&::-webkit-details-marker]:hidden">
        {line}
        <span className="text-muted-foreground hover:text-foreground mt-0.5 inline-flex items-center gap-1 text-xs">
          <span className="group-open:hidden">Show feedback</span>
          <span className="hidden group-open:inline">Hide feedback</span>
          <ChevronDown className="size-3.5 transition-transform group-open:rotate-180" />
        </span>
      </summary>
      <blockquote className="text-foreground/85 mt-2 rounded-lg border border-[oklch(0.93_0.035_85)] bg-[oklch(0.985_0.012_85)] px-3 py-2 text-[12.5px] leading-normal whitespace-pre-line">
        {comment}
      </blockquote>
    </details>
  );
}
