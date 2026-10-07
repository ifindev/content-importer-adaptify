"use server";

import { revalidatePath } from "next/cache";

import type { Schemas } from "@/lib/api/types";
import { mutationFailure } from "@/lib/fixtures/scenario";
import { newId, now } from "@/lib/fixtures/store";
import type { MutationResult } from "@/lib/mutation-result";

import { reviewArticles } from "./review.queries";

async function decide(
  token: string,
  id: string,
  version: number,
  clientName: string,
  status: "approved" | "changes_requested",
  comment?: string,
): Promise<MutationResult<Schemas["ReviewActionOut"]>> {
  const failure = await mutationFailure();
  if (failure) return failure;
  const { siteId, articles } = await reviewArticles(token);
  const article = articles.find((a) => a.id === id);
  if (!article) return { ok: false, code: "not_found" };
  if (article.status !== "awaiting_approval")
    return { ok: false, code: "not_awaiting_approval" };
  if (article.version !== version)
    return { ok: false, code: "article_changed" };
  Object.assign(article, {
    status,
    updated_at: now(),
    ...(status === "approved"
      ? { approved_version: version }
      : { client_comment: comment }),
  });
  article.events.push({
    id: newId(),
    type: status,
    actor: clientName,
    at: now(),
  });
  revalidatePath(`/review/${token}`, "layout");
  revalidatePath(`/sites/${siteId}`, "layout");
  return { ok: true, data: { id, status } };
}

export async function approve(
  token: string,
  id: string,
  form: Schemas["ApproveRequest"],
) {
  return decide(token, id, form.version, form.client_name, "approved");
}

export async function requestChanges(
  token: string,
  id: string,
  form: Schemas["RequestChangesRequest"],
) {
  return decide(
    token,
    id,
    form.version,
    form.client_name,
    "changes_requested",
    form.comment,
  );
}
