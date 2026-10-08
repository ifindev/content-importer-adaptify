import "server-only";

import { notFound } from "next/navigation";

import { apiServer } from "@/lib/api-server";
import type { Schemas } from "@/lib/api/types";
import { ApiError } from "@/lib/http";
import { orNotFound } from "@/lib/mutation-result";

/**
 * Token-only reads: no session. A 429 comes back as `null` for the page to
 * render the rate-limit state; a thrown error's message is hidden in
 * production builds, so error.tsx can't tell a 429 apart.
 */
async function orRateLimited<T>(call: Promise<T>): Promise<T | null> {
  try {
    return await orNotFound(call, notFound);
  } catch (error) {
    if (error instanceof ApiError && error.status === 429) return null;
    throw error;
  }
}

export async function getReview(
  token: string,
): Promise<Schemas["ReviewPageOut"] | null> {
  return orRateLimited((await apiServer()).get(`/review/${token}`));
}

export async function getReviewArticle(
  token: string,
  id: string,
): Promise<Schemas["ReviewArticleOut"] | null> {
  return orRateLimited(
    (await apiServer()).get(`/review/${token}/articles/${id}`),
  );
}
