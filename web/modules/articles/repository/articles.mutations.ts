"use server";

import { revalidatePath } from "next/cache";

import { apiServer } from "@/lib/api-server";
import type { Schemas } from "@/lib/api/types";
import { toResult, type MutationResult } from "@/lib/mutation-result";

type Article = Schemas["ArticleDetail"];

function revalidate(siteId: string, id?: string) {
  revalidatePath(`/sites/${siteId}/articles`);
  if (id) revalidatePath(`/sites/${siteId}/articles/${id}`);
  revalidatePath(`/sites/${siteId}/report`);
  revalidatePath("/review", "layout");
}

/** Runs `call` and revalidates the site's pages when it succeeds. */
async function mutate<T>(
  siteId: string,
  id: string | undefined,
  call: Promise<T>,
): Promise<MutationResult<T>> {
  const result = await toResult(call);
  if (result.ok) revalidate(siteId, id);
  return result;
}

const base = (siteId: string) => `/sites/${siteId}/articles`;

export async function pasteArticle(
  siteId: string,
  form: Schemas["ArticlePaste"],
): Promise<MutationResult<Schemas["ArticleSummary"]>> {
  const api = await apiServer();
  return mutate(siteId, undefined, api.post(`${base(siteId)}/paste`, form));
}

export async function uploadArticles(
  siteId: string,
  formData: FormData,
): Promise<MutationResult<Schemas["UploadResponse"]>> {
  const api = await apiServer();
  return mutate(
    siteId,
    undefined,
    api.postForm(`${base(siteId)}/upload`, formData),
  );
}

export async function updateArticle(
  siteId: string,
  id: string,
  form: Schemas["ArticleUpdate"],
): Promise<MutationResult<Article>> {
  const api = await apiServer();
  return mutate(siteId, id, api.patch(`${base(siteId)}/${id}`, form));
}

export async function sendForReview(
  siteId: string,
  id: string,
): Promise<MutationResult<Article>> {
  const api = await apiServer();
  return mutate(siteId, id, api.post(`${base(siteId)}/${id}/send-for-review`));
}

export async function pullBack(
  siteId: string,
  id: string,
): Promise<MutationResult<Article>> {
  const api = await apiServer();
  return mutate(siteId, id, api.post(`${base(siteId)}/${id}/pull-back`));
}

export async function scheduleArticle(
  siteId: string,
  id: string,
  publishAt: string,
): Promise<MutationResult<Article>> {
  const api = await apiServer();
  const body: Schemas["ScheduleRequest"] = { publish_at: publishAt };
  return mutate(siteId, id, api.post(`${base(siteId)}/${id}/schedule`, body));
}

export async function retryArticle(
  siteId: string,
  id: string,
): Promise<MutationResult<Article>> {
  const api = await apiServer();
  return mutate(siteId, id, api.post(`${base(siteId)}/${id}/retry`));
}

export async function resetReviewLink(
  siteId: string,
): Promise<MutationResult<Schemas["ReviewLinkOut"]>> {
  const api = await apiServer();
  return mutate(
    siteId,
    undefined,
    api.post(`/sites/${siteId}/review-link/reset`),
  );
}

export async function deleteArticle(
  siteId: string,
  id: string,
): Promise<MutationResult<null>> {
  const api = await apiServer();
  return mutate(siteId, undefined, api.delete<null>(`${base(siteId)}/${id}`));
}
