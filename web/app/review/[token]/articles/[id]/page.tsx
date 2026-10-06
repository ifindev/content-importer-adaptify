import { ReviewArticlePage } from "@/modules/review/pages/ReviewArticlePage";
import type { PageProps } from "@/lib/types/page-props";

export default async function Page({
  params,
}: PageProps<{ token: string; id: string }>) {
  const { token, id } = await params;
  return <ReviewArticlePage token={token} articleId={id} />;
}
