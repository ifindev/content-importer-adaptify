import { ArticlesPage } from "@/modules/articles/pages/ArticlesPage";

export default async function Page({
  params,
  searchParams,
}: PageProps<"/sites/[siteId]/articles">) {
  const { siteId } = await params;
  const { status, q } = await searchParams;
  return (
    <ArticlesPage
      siteId={siteId}
      status={typeof status === "string" ? status : undefined}
      query={typeof q === "string" ? q : ""}
    />
  );
}
