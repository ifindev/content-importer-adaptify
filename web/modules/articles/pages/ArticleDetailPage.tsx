import { getArticle } from "@/modules/articles/data";
import { ArticleDetail } from "@/modules/articles/components/ArticleDetail";
import { listSites } from "@/modules/sites/data";

export async function ArticleDetailPage({
  siteId,
  articleId,
}: {
  siteId: string;
  articleId: string;
}) {
  const [article, { sites }] = await Promise.all([
    getArticle(siteId, articleId),
    listSites(),
  ]);
  const site = sites.find((s) => s.id === siteId);

  return (
    <ArticleDetail
      // A new version from the server (after save or a status change)
      // resets the editor's local state.
      key={`${article.id}-${article.version}-${article.status}`}
      siteId={siteId}
      siteHost={site?.wp_base_url.replace(/^https?:\/\//, "") ?? ""}
      article={article}
    />
  );
}
