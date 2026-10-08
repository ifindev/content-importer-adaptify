import "server-only";

import { notFound } from "next/navigation";

import { apiServer } from "@/lib/api-server";
import type { Schemas } from "@/lib/api/types";
import { orNotFound } from "@/lib/mutation-result";

// Token-only: no session. A 429 throws to error.tsx.
export async function getReview(
  token: string,
): Promise<Schemas["ReviewPageOut"]> {
  return orNotFound((await apiServer()).get(`/review/${token}`), notFound);
}

export async function getReviewArticle(
  token: string,
  id: string,
): Promise<Schemas["ReviewArticleOut"]> {
  return orNotFound(
    (await apiServer()).get(`/review/${token}/articles/${id}`),
    notFound,
  );
}
