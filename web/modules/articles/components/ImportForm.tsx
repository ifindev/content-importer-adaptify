"use client";

import {
  CircleAlert,
  CircleCheck,
  FileText,
  Loader2,
  TriangleAlert,
  Upload,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { toast } from "sonner";

import { ArticleEditor } from "@/components/article-editor";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { Schemas } from "@/lib/api/types";
import { messageFor } from "@/lib/error-messages";
import { cn } from "@/lib/utils";
import {
  deleteArticle,
  pasteArticle,
  uploadArticles,
} from "@/modules/articles/actions";

import { ConfirmDeleteDialog } from "./ConfirmDeleteDialog";

type Tab = "paste" | "upload";

export function ImportForm({ siteId }: { siteId: string }) {
  const [tab, setTab] = useState<Tab>("paste");

  return (
    <>
      <div
        role="tablist"
        aria-label="Import method"
        className="bg-muted flex w-fit gap-0.5 rounded-[9px] p-[3px]"
      >
        {(["paste", "upload"] as const).map((value) => (
          <button
            key={value}
            role="tab"
            id={`tab-${value}`}
            aria-selected={tab === value}
            aria-controls={`panel-${value}`}
            onClick={() => setTab(value)}
            className={cn(
              "text-foreground/65 focus-visible:ring-ring/50 h-7 rounded-[7px] px-3 text-[13px] font-medium outline-none focus-visible:ring-3",
              tab === value &&
                "bg-background text-foreground shadow-[0_0_0_1px_var(--border),0_1px_2px_oklch(0_0_0/0.06)]",
            )}
          >
            {value === "paste" ? "Paste" : "Upload .docx"}
          </button>
        ))}
      </div>
      <div role="tabpanel" id={`panel-${tab}`} aria-labelledby={`tab-${tab}`}>
        {tab === "paste" ? (
          <PastePanel siteId={siteId} />
        ) : (
          <UploadPanel siteId={siteId} />
        )}
      </div>
    </>
  );
}

const escapeHtml = (text: string) =>
  text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

function ErrorAlert({ code }: { code: string }) {
  return (
    <div
      role="alert"
      className="flex gap-2.5 rounded-[9px] border border-[oklch(0.91_0.045_27.325)] bg-[oklch(0.97_0.015_27.325)] px-3 py-2.5 text-[13px] text-[oklch(0.42_0.17_27.325)]"
    >
      <CircleAlert className="mt-px size-4 shrink-0" />
      {messageFor(code)}
    </div>
  );
}

function PastePanel({ siteId }: { siteId: string }) {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [html, setHtml] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  function submit() {
    setError(null);
    startTransition(async () => {
      // The server takes the first heading as the title (spec R1.5), so an
      // explicit title goes first as an h1.
      const heading = title.trim()
        ? `<h1>${escapeHtml(title.trim())}</h1>`
        : "";
      const result = await pasteArticle(siteId, { html: heading + html });
      if (!result.ok) {
        setError(result.code);
        return;
      }
      toast.success("Article imported.");
      router.push(`/sites/${siteId}/articles/${result.data.id}`);
    });
  }

  return (
    <div className="flex flex-col gap-4">
      {error && <ErrorAlert code={error} />}
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="paste-title">Title</Label>
        <Input
          id="paste-title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Leave empty to use the first heading"
        />
      </div>
      <div className="overflow-hidden rounded-xl border shadow-xs">
        <ArticleEditor
          content=""
          onChange={setHtml}
          label="Paste the article here"
          className="[&_.ProseMirror]:min-h-64"
        />
      </div>
      <div className="flex items-center justify-end gap-3">
        <span className="text-muted-foreground mr-auto text-[12.5px]">
          Headings, lists, links and tables are kept. Fonts and colors are
          stripped.
        </span>
        <Button onClick={submit} disabled={pending}>
          {pending && <Loader2 className="animate-spin" />}
          Import article
        </Button>
      </div>
    </div>
  );
}

function UploadPanel({ siteId }: { siteId: string }) {
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<Schemas["UploadFileResult"][]>([]);
  const [dragging, setDragging] = useState(false);
  const [pending, startTransition] = useTransition();
  const [toDelete, setToDelete] = useState<Schemas["UploadFileResult"] | null>(
    null,
  );
  const [deleting, startDelete] = useTransition();
  const imported = results.filter((r) => r.ok).length;

  function confirmDelete() {
    const target = toDelete;
    if (!target?.article) return;
    const id = target.article.id;
    startDelete(async () => {
      const result = await deleteArticle(siteId, id);
      if (!result.ok) {
        toast.error(messageFor(result.code));
        return;
      }
      setResults((prev) => prev.filter((r) => r !== target));
      setToDelete(null);
      toast.success("Draft deleted.");
    });
  }

  function upload(files: FileList | null) {
    if (!files) return;
    const formData = new FormData();
    for (const file of files) formData.append("files", file);
    setError(null);
    startTransition(async () => {
      const result = await uploadArticles(siteId, formData);
      if (!result.ok) {
        setError(result.code);
        return;
      }
      setResults((prev) => [...result.data.results, ...prev]);
    });
  }

  return (
    <div className="flex flex-col gap-5">
      {error && <ErrorAlert code={error} />}
      <label
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          upload(e.dataTransfer.files);
        }}
        className={cn(
          "has-focus-visible:ring-ring/50 flex h-[196px] cursor-pointer flex-col items-center justify-center gap-0.5 rounded-xl border border-dashed border-[oklch(0.86_0.004_264)] bg-[oklch(0.99_0_0)] text-center hover:border-[oklch(0.8_0.004_264)] hover:bg-[oklch(0.98_0_0)] has-focus-visible:ring-3",
          dragging && "border-primary/60 bg-primary/5",
          pending && "pointer-events-none opacity-70",
        )}
      >
        <span className="bg-background mb-3 flex size-10 items-center justify-center rounded-[10px] border shadow-xs">
          {pending ? (
            <Loader2 className="size-[18px] animate-spin" />
          ) : (
            <Upload className="size-[18px]" />
          )}
        </span>
        <span className="text-sm font-medium">
          {pending ? (
            "Uploading…"
          ) : (
            <>
              Drop .docx files here, or{" "}
              <span className="underline underline-offset-[3px]">browse</span>
            </>
          )}
        </span>
        <span className="text-muted-foreground text-[12.5px]">
          Each file becomes one Draft article · up to 10 files
        </span>
        <input
          type="file"
          accept=".docx"
          multiple
          className="sr-only"
          onChange={(e) => {
            upload(e.target.files);
            e.target.value = "";
          }}
        />
      </label>

      {imported > 0 && (
        <div
          role="status"
          className="bg-status-awaiting text-status-awaiting-fg flex flex-wrap items-center gap-x-2 gap-y-1 rounded-[9px] px-3 py-2.5 text-[13px]"
        >
          <CircleCheck className="size-4 shrink-0" />
          {imported} {imported === 1 ? "article was" : "articles were"} added as
          Drafts.{" "}
          <Link
            href={`/sites/${siteId}/articles`}
            className="font-medium underline underline-offset-[3px]"
          >
            See them in Articles →
          </Link>
        </div>
      )}

      {results.length > 0 && (
        <section>
          <div className="mb-2.5 flex items-baseline gap-2">
            <h2 className="text-sm font-semibold">Just imported</h2>
            <span className="text-muted-foreground text-[12.5px]">
              {results.length} {results.length === 1 ? "file" : "files"}
            </span>
          </div>
          <ul className="rounded-[10px] border shadow-xs">
            {results.map((r, i) => (
              <li
                key={`${r.filename}-${i}`}
                className="flex items-center gap-3 border-t border-[oklch(0.955_0.003_264)] px-3.5 py-3 first:border-t-0"
              >
                <span
                  className={cn(
                    "flex size-8 shrink-0 items-center justify-center rounded-lg",
                    r.ok
                      ? "bg-muted text-foreground/60"
                      : "bg-status-failed text-status-failed-fg",
                  )}
                >
                  <FileText className="size-4" />
                </span>
                <div className="min-w-0 flex-1">
                  <div className="truncate text-[13.5px] font-medium">
                    {r.filename}
                  </div>
                  {r.ok && (
                    <div className="text-muted-foreground flex items-center gap-1.5 text-[12.5px]">
                      <CircleCheck className="size-3.5 text-emerald-600" />{" "}
                      Converted to a Draft
                    </div>
                  )}
                  {r.ok && r.warnings.length > 0 && (
                    <ul className="text-status-changes-fg mt-0.5 flex flex-col gap-0.5 text-[12.5px]">
                      {r.warnings.map((w) => (
                        <li key={w} className="flex gap-1.5">
                          <TriangleAlert className="mt-0.5 size-3.5 shrink-0" />
                          {w}
                        </li>
                      ))}
                    </ul>
                  )}
                  {!r.ok && (
                    <div className="text-status-failed-fg text-[12.5px]">
                      {messageFor(r.code ?? "")}
                    </div>
                  )}
                </div>
                {r.ok && r.article ? (
                  <div className="flex shrink-0 gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      aria-label={`Delete ${r.filename}`}
                      onClick={() => setToDelete(r)}
                    >
                      Delete
                    </Button>
                    <Link
                      href={`/sites/${siteId}/articles/${r.article.id}`}
                      className={buttonVariants({
                        variant: "outline",
                        size: "sm",
                      })}
                    >
                      Open
                    </Link>
                  </div>
                ) : (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() =>
                      setResults((prev) => prev.filter((_, j) => j !== i))
                    }
                  >
                    Remove
                  </Button>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}
      <ConfirmDeleteDialog
        open={toDelete !== null}
        onOpenChange={(open) => !open && setToDelete(null)}
        count={1}
        title={toDelete?.article?.title}
        pending={deleting}
        onConfirm={confirmDelete}
      />
    </div>
  );
}
