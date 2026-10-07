import { ImportPage } from "@/modules/articles/pages/ImportPage";

export default async function Page({
  params,
}: PageProps<"/sites/[siteId]/import">) {
  const { siteId } = await params;
  return <ImportPage siteId={siteId} />;
}
