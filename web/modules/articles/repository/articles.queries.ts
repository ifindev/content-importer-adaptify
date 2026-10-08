import "server-only";

import { notFound } from "next/navigation";

import { apiServer } from "@/lib/api-server";
import type { Schemas } from "@/lib/api/types";
import { orNotFound } from "@/lib/mutation-result";

export async function listArticles(
  siteId: string,
  status?: Schemas["Status"],
): Promise<Schemas["ArticlesOut"]> {
  const query = status ? `?status=${status}` : "";
  return orNotFound(
    (await apiServer()).get(`/sites/${siteId}/articles${query}`),
    notFound,
  );
}

export async function getArticle(
  siteId: string,
  id: string,
): Promise<Schemas["ArticleDetail"]> {
  return orNotFound(
    (await apiServer()).get(`/sites/${siteId}/articles/${id}`),
    notFound,
  );
}

export async function getReviewLink(
  siteId: string,
): Promise<Schemas["ReviewLinkOut"]> {
  return orNotFound(
    (await apiServer()).get(`/sites/${siteId}/review-link`),
    notFound,
  );
}
