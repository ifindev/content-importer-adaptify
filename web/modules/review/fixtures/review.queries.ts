import "server-only";

import { notFound } from "next/navigation";

import type { Schemas } from "@/lib/api/types";
import { readDelay, scenario } from "@/lib/fixtures/scenario";
import { db } from "@/lib/fixtures/store";

export async function reviewArticles(token: string) {
  if ((await scenario()) === "rate-limited") throw new Error("rate_limited");
  const siteId = db.reviewTokens[token];
  if (!siteId) notFound();
  return { siteId, articles: db.articles[siteId] };
}

const card = (a: Schemas["ArticleDetail"]): Schemas["ArticleCard"] => ({
  id: a.id,
  title: a.title,
  slug: a.slug,
  publish_at_utc: a.publish_at_utc,
  published_url: a.published_url,
  sync_warning: a.sync_warning,
});

export async function getReview(
  token: string,
): Promise<Schemas["ReviewPageOut"]> {
  await readDelay();
  const { siteId, articles: all } = await reviewArticles(token);
  const current = await scenario();
  const articles = current === "empty" ? [] : all;
  return {
    site_name: db.sites.find((s) => s.id === siteId)?.name ?? siteId,
    waiting: articles.filter((a) => a.status === "awaiting_approval").map(card),
    upcoming: articles
      .filter((a) => a.status === "approved" || a.status === "scheduled")
      .map(card),
    published: articles.filter((a) => a.status === "published").map(card),
    wordpress_unreachable: current === "wordpress-down",
  };
}

const VISIBLE: Schemas["Status"][] = [
  "awaiting_approval",
  "approved",
  "scheduled",
  "published",
];

export async function getReviewArticle(
  token: string,
  id: string,
): Promise<Schemas["ReviewArticleOut"]> {
  await readDelay();
  const { articles } = await reviewArticles(token);
  const a = articles.find((x) => x.id === id && VISIBLE.includes(x.status));
  if (!a) notFound();
  return {
    id: a.id,
    title: a.title,
    slug: a.slug,
    body_html: a.body_html,
    status: a.status,
    version: a.version,
  };
}
