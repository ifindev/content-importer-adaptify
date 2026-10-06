import { ReviewPage } from "@/modules/review/pages/ReviewPage";
import type { PageProps } from "@/lib/types/page-props";

export default async function Page({ params }: PageProps<{ token: string }>) {
  const { token } = await params;
  return <ReviewPage token={token} />;
}
