import "server-only";

import { notFound } from "next/navigation";

import type { Schemas } from "@/lib/api/types";
import { readDelay, scenario } from "@/lib/fixtures/scenario";
import { db } from "@/lib/fixtures/store";

export function siteArticles(siteId: string) {
  const articles = db.articles[siteId];
  if (!articles) notFound();
  return articles;
}

function summary(a: Schemas["ArticleDetail"]): Schemas["ArticleSummary"] {
  return {
    id: a.id,
    title: a.title,
    slug: a.slug,
    status: a.status,
    sync_warning: a.sync_warning,
    publish_at_utc: a.publish_at_utc,
    updated_at: a.updated_at,
  };
}

export async function listArticles(
  siteId: string,
  status?: Schemas["Status"],
): Promise<Schemas["ArticlesOut"]> {
  await readDelay();
  const current = await scenario();
  const articles = current === "empty" ? [] : siteArticles(siteId);
  return {
    articles: articles
      .filter((a) => !status || a.status === status)
      .map(summary),
    wordpress_unreachable: current === "wordpress-down",
  };
}

export async function getArticle(
  siteId: string,
  id: string,
): Promise<Schemas["ArticleDetail"]> {
  await readDelay();
  const article = siteArticles(siteId).find((a) => a.id === id);
  if (!article) notFound();
  return article;
}

export async function getReviewLink(
  siteId: string,
): Promise<Schemas["ReviewLinkOut"]> {
  siteArticles(siteId);
  const token =
    Object.entries(db.reviewTokens).find(([, site]) => site === siteId)?.[0] ??
    `token-${siteId}`;
  return {
    url: `http://localhost:3000/review/${token}`,
    created_at: db.reviewLinkCreatedAt,
  };
}

export { summary };
