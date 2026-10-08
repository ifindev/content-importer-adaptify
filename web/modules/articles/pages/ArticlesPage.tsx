import { Download, FileText, SearchX } from "lucide-react";
import Link from "next/link";

import { PageHeader } from "@/components/page-header";
import { buttonVariants } from "@/components/ui/button";
import { WordPressBanner } from "@/components/wordpress-banner";
import type { Schemas } from "@/lib/api/types";
import { ArticleFilters } from "@/modules/articles/components/ArticleFilters";
import { ArticleTable } from "@/modules/articles/components/ArticleTable";
import { ReviewLinkActions } from "@/modules/articles/components/ReviewLinkActions";
import { getReviewLink, listArticles } from "@/modules/articles/data";

type Summary = Schemas["ArticleSummary"];

const needsAttention = (a: Summary) =>
  a.status === "failed" || !!a.sync_warning;

export async function ArticlesPage({
  siteId,
  status,
  query,
}: {
  siteId: string;
  status: string | undefined;
  query: string;
}) {
  const [{ articles, wordpress_unreachable }, reviewLink] = await Promise.all([
    listArticles(siteId),
    getReviewLink(siteId),
  ]);

  const counts: Record<string, number> = { needs_attention: 0 };
  for (const a of articles) {
    counts[a.status] = (counts[a.status] ?? 0) + 1;
    if (needsAttention(a)) counts.needs_attention += 1;
  }
  const q = query.trim().toLowerCase();
  const shown = articles.filter(
    (a) =>
      (!status ||
        a.status === status ||
        (status === "needs_attention" && needsAttention(a))) &&
      (!q || a.title.toLowerCase().includes(q)),
  );
  const base = `/sites/${siteId}/articles`;

  return (
    <>
      <PageHeader
        title="Articles"
        subtitle={`${articles.length} ${articles.length === 1 ? "article" : "articles"} on this site`}
      >
        <ReviewLinkActions siteId={siteId} url={reviewLink.url} />
      </PageHeader>
      {wordpress_unreachable && (
        <div className="px-4 pt-3 md:px-7">
          <WordPressBanner />
        </div>
      )}
      {articles.length === 0 ? (
        <EmptyState
          icon={<FileText />}
          title="No articles yet"
          body="Paste an article or upload .docx files to get started."
        >
          <Link href={`/sites/${siteId}/import`} className={buttonVariants()}>
            <Download /> Import
          </Link>
        </EmptyState>
      ) : (
        <>
          <ArticleFilters status={status} query={query} counts={counts} />
          {shown.length === 0 ? (
            <EmptyState
              icon={<SearchX />}
              title="No articles match"
              body="Try another status or search term."
            >
              <Link
                href={base}
                className={buttonVariants({ variant: "outline" })}
              >
                Clear filters
              </Link>
            </EmptyState>
          ) : (
            <ArticleTable siteId={siteId} articles={shown} />
          )}
        </>
      )}
    </>
  );
}

export function EmptyState({
  icon,
  title,
  body,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  body: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center px-6 py-16 text-center">
      <span className="bg-background text-foreground/70 mb-4 flex size-11 items-center justify-center rounded-xl border shadow-xs [&_svg]:size-5">
        {icon}
      </span>
      <h2 className="text-[15px] font-semibold">{title}</h2>
      <p className="text-muted-foreground mt-1 max-w-sm text-[13.5px]">
        {body}
      </p>
      {children && <div className="mt-5">{children}</div>}
    </div>
  );
}
