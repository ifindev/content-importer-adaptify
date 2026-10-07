import "server-only";

import { notFound } from "next/navigation";

import type { Schemas } from "@/lib/api/types";
import { readDelay, scenario } from "@/lib/fixtures/scenario";
import { db } from "@/lib/fixtures/store";

export async function getReport(siteId: string): Promise<Schemas["ReportOut"]> {
  await readDelay();
  const current = await scenario();
  if (!db.articles[siteId]) notFound();
  const articles = current === "empty" ? [] : db.articles[siteId];

  const statusCounts: Record<string, number> = {};
  for (const a of articles)
    statusCounts[a.status] = (statusCounts[a.status] ?? 0) + 1;

  const monthStart = new Date();
  monthStart.setUTCDate(1);
  monthStart.setUTCHours(0, 0, 0, 0);
  const published = articles
    .filter((a) => a.status === "published" && a.published_url)
    .map((a) => ({
      article_id: a.id,
      title: a.title,
      published_at: a.publish_at_utc ?? a.updated_at,
      published_url: a.published_url!,
    }))
    .sort((x, y) => y.published_at.localeCompare(x.published_at));

  return {
    status_counts: statusCounts,
    published_this_month: published.filter(
      (p) => new Date(p.published_at) >= monthStart,
    ).length,
    // A fixed figure: the fixtures don't model approval timing.
    avg_approval_seconds: articles.length ? 2.4 * 86400 : null,
    wordpress_unreachable: current === "wordpress-down",
    upcoming: articles
      .filter((a) => a.status === "scheduled" && a.publish_at_utc)
      .map((a) => ({
        article_id: a.id,
        title: a.title,
        publish_at_utc: a.publish_at_utc!,
      }))
      .sort((x, y) => x.publish_at_utc.localeCompare(y.publish_at_utc)),
    published,
    needs_attention: articles.flatMap((a): Schemas["NeedsAttentionEntry"][] =>
      a.status === "failed"
        ? [
            {
              article_id: a.id,
              title: a.title,
              reason: "failed",
              detail: a.last_error,
            },
          ]
        : a.sync_warning
          ? [{ article_id: a.id, title: a.title, reason: a.sync_warning }]
          : [],
    ),
    change_rounds: articles
      .filter((a) => a.version > 1 || a.status === "changes_requested")
      .map((a) => ({
        article_id: a.id,
        title: a.title,
        rounds: a.status === "changes_requested" ? a.version : a.version - 1,
      })),
  };
}
