import { ReportPage } from "@/modules/report/pages/ReportPage";

export default async function Page({
  params,
}: PageProps<"/sites/[siteId]/report">) {
  const { siteId } = await params;
  return <ReportPage siteId={siteId} />;
}
