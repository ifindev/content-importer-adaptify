import "server-only";

import { readDelay, scenario } from "@/lib/fixtures/scenario";
import { db, type FixtureSite } from "@/lib/fixtures/store";

const NEEDS_ATTENTION = new Set(["failed"]);

export type SiteWithStats = FixtureSite & {
  article_count: number;
  needs_attention_count: number;
};

export async function listSites(): Promise<{ sites: SiteWithStats[] }> {
  await readDelay();
  const current = await scenario();
  if (current === "no-sites") return { sites: [] };
  const sites = current === "one-site" ? db.sites.slice(0, 1) : db.sites;
  return {
    sites: sites.map((site) => {
      const articles = db.articles[site.id] ?? [];
      return {
        ...site,
        article_count: articles.length,
        needs_attention_count: articles.filter(
          (a) => NEEDS_ATTENTION.has(a.status) || a.sync_warning,
        ).length,
      };
    }),
  };
}
