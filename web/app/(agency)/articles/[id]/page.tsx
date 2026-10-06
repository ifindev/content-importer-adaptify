import { ArticleDetailPage } from "@/modules/articles/pages/ArticleDetailPage";
import type { PageProps } from "@/lib/types/page-props";

export default async function Page({ params }: PageProps<{ id: string }>) {
  const { id } = await params;
  return <ArticleDetailPage articleId={id} />;
}
