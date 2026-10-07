"use server";

import { revalidatePath } from "next/cache";

import type { Schemas } from "@/lib/api/types";
import { mutationFailure } from "@/lib/fixtures/scenario";
import { db, newId, now } from "@/lib/fixtures/store";
import type { MutationResult } from "@/lib/mutation-result";

import { siteArticles, summary } from "./articles.queries";

type Article = Schemas["ArticleDetail"];

const PASTE_MAX_BYTES = 2 * 1024 * 1024;
const UPLOAD_MAX_FILES = 10;
const UPLOAD_MAX_FILE_BYTES = 10 * 1024 * 1024;

function revalidate(siteId: string, id?: string) {
  revalidatePath(`/sites/${siteId}/articles`);
  if (id) revalidatePath(`/sites/${siteId}/articles/${id}`);
  revalidatePath(`/sites/${siteId}/report`);
  revalidatePath("/review", "layout");
}

function create(siteId: string, fields: Partial<Article>): Article {
  const title = fields.title ?? "Untitled";
  const article: Article = {
    id: newId(),
    title,
    slug: title.toLowerCase().replace(/[^a-z0-9]+/g, "-"),
    body_html: "<p></p>",
    status: "draft",
    version: 1,
    source: "paste",
    warnings: [],
    events: [{ id: newId(), type: "imported", actor: "agency", at: now() }],
    created_at: now(),
    updated_at: now(),
    ...fields,
  };
  siteArticles(siteId).unshift(article);
  return article;
}

/** Applies a status change with its history entry, or returns `code`. */
function transition(
  siteId: string,
  id: string,
  from: Article["status"][],
  code: string,
  change: (a: Article) => Partial<Article> & { status: Article["status"] },
  event: Schemas["EventType"],
): MutationResult<Article> {
  const article = siteArticles(siteId).find((a) => a.id === id);
  if (!article) return { ok: false, code: "not_found" };
  if (!from.includes(article.status)) return { ok: false, code };
  Object.assign(article, change(article), { updated_at: now() });
  article.events.push({ id: newId(), type: event, actor: "agency", at: now() });
  revalidate(siteId, id);
  return { ok: true, data: article };
}

export async function pasteArticle(
  siteId: string,
  form: Schemas["ArticlePaste"],
): Promise<MutationResult<Schemas["ArticleSummary"]>> {
  const failure = await mutationFailure();
  if (failure) return failure;
  const text = form.html.replace(/<[^>]*>/g, "").trim();
  if (!text) return { ok: false, code: "empty_content" };
  if (new Blob([form.html]).size > PASTE_MAX_BYTES)
    return { ok: false, code: "payload_too_large" };
  // Same rule as the server's parser (spec R1.5): the first heading of any
  // level is the title and is removed from the body.
  const heading = form.html.match(/<h([1-6])[^>]*>([\s\S]*?)<\/h\1>/i);
  const article = create(siteId, {
    title: heading?.[2].replace(/<[^>]*>/g, "").trim() || "Untitled",
    body_html: heading ? form.html.replace(heading[0], "") : form.html,
  });
  revalidate(siteId);
  return { ok: true, data: summary(article) };
}

export async function uploadArticles(
  siteId: string,
  formData: FormData,
): Promise<MutationResult<Schemas["UploadResponse"]>> {
  const failure = await mutationFailure();
  if (failure) return failure;
  const files = formData
    .getAll("files")
    .filter((f): f is File => f instanceof File && f.name !== "");
  if (files.length === 0) return { ok: false, code: "no_files" };
  if (files.length > UPLOAD_MAX_FILES)
    return { ok: false, code: "too_many_files" };

  const results = files.map((file): Schemas["UploadFileResult"] => {
    if (!file.name.toLowerCase().endsWith(".docx"))
      return { filename: file.name, ok: false, code: "unsupported_file_type" };
    if (file.size > UPLOAD_MAX_FILE_BYTES)
      return { filename: file.name, ok: false, code: "file_too_large" };
    // ponytail: fixtures can't parse .docx; an empty or "unreadable" file
    // stands in for a corrupt one.
    if (file.size === 0 || file.name.includes("unreadable"))
      return { filename: file.name, ok: false, code: "unreadable_file" };
    const article = create(siteId, {
      title: file.name.replace(/\.docx$/i, "").replace(/[-_]+/g, " "),
      body_html:
        "<h2>Imported document</h2><p>Converted text from the uploaded file.</p>",
      source: "docx",
      source_filename: file.name,
      warnings: file.name.includes("images")
        ? ["This document had 3 images. Images are not imported."]
        : [],
    });
    return { filename: file.name, ok: true, article: summary(article) };
  });
  revalidate(siteId);
  return { ok: true, data: { results } };
}

export async function updateArticle(
  siteId: string,
  id: string,
  form: Schemas["ArticleUpdate"],
): Promise<MutationResult<Article>> {
  const failure = await mutationFailure();
  if (failure) return failure;
  if (form.title == null && form.slug == null && form.body_html == null)
    return { ok: false, code: "empty_update" };
  if (form.body_html != null && !form.body_html.replace(/<[^>]*>/g, "").trim())
    return { ok: false, code: "empty_content" };
  return transition(
    siteId,
    id,
    ["draft", "changes_requested", "approved", "scheduled"],
    "not_editable",
    (a) => ({
      ...Object.fromEntries(
        Object.entries(form).filter(([, value]) => value != null),
      ),
      version: a.version + 1,
      client_comment: null,
      // Edits reset approval (spec: Approval rules).
      status: a.status === "changes_requested" ? a.status : "draft",
      ...(a.status === "scheduled" ? { publish_at_utc: null } : {}),
    }),
    "edited",
  );
}

export async function sendForReview(siteId: string, id: string) {
  const failure = await mutationFailure();
  if (failure) return failure;
  return transition(
    siteId,
    id,
    ["draft", "changes_requested"],
    "not_sendable",
    () => ({ status: "awaiting_approval", client_comment: null }),
    "sent_for_review",
  );
}

export async function pullBack(siteId: string, id: string) {
  const failure = await mutationFailure();
  if (failure) return failure;
  return transition(
    siteId,
    id,
    ["awaiting_approval"],
    "not_awaiting_approval",
    () => ({ status: "draft" }),
    "pulled_back",
  );
}

export async function scheduleArticle(
  siteId: string,
  id: string,
  publishAt: string,
) {
  const failure = await mutationFailure();
  if (failure) return failure;
  if (new Date(publishAt).getTime() < Date.now())
    return { ok: false as const, code: "publish_at_in_past" };
  return transition(
    siteId,
    id,
    ["approved", "scheduled"],
    "not_schedulable",
    (a) => ({
      status: "scheduled",
      publish_at_utc: publishAt,
      sync_warning: null,
      wp_post_id: a.wp_post_id ?? 500,
    }),
    "scheduled",
  );
}

export async function retryArticle(siteId: string, id: string) {
  const failure = await mutationFailure();
  if (failure) return failure;
  return transition(
    siteId,
    id,
    ["failed"],
    "not_failed",
    (a) => ({
      status: "scheduled",
      last_error: null,
      publish_at_utc:
        a.publish_at_utc ?? new Date(Date.now() + 864e5).toISOString(),
    }),
    "retried",
  );
}

export async function resetReviewLink(
  siteId: string,
): Promise<MutationResult<Schemas["ReviewLinkOut"]>> {
  const failure = await mutationFailure();
  if (failure) return failure;
  siteArticles(siteId);
  const token = `${siteId}-${Math.random().toString(36).slice(2, 8)}`;
  for (const [key, site] of Object.entries(db.reviewTokens)) {
    if (site === siteId) delete db.reviewTokens[key];
  }
  db.reviewTokens[token] = siteId;
  db.reviewLinkCreatedAt = now();
  revalidate(siteId);
  return {
    ok: true,
    data: {
      url: `http://localhost:3000/review/${token}`,
      created_at: db.reviewLinkCreatedAt,
    },
  };
}

export async function deleteArticle(
  siteId: string,
  id: string,
): Promise<MutationResult<null>> {
  const failure = await mutationFailure();
  if (failure) return failure;
  const articles = siteArticles(siteId);
  const index = articles.findIndex((a) => a.id === id);
  if (index === -1) return { ok: false, code: "not_found" };
  if (!["draft", "changes_requested"].includes(articles[index].status))
    return { ok: false, code: "not_deletable" };
  articles.splice(index, 1);
  revalidate(siteId);
  return { ok: true, data: null };
}
