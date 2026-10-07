import { ArticleDetailPage } from "@/modules/articles/pages/ArticleDetailPage";

export default async function Page({
  params,
}: PageProps<"/sites/[siteId]/articles/[id]">) {
  const { siteId, id } = await params;
  return <ArticleDetailPage siteId={siteId} articleId={id} />;
}
