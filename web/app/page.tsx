import { redirect } from "next/navigation";

import { listSites } from "@/modules/sites/data";

export default async function Page() {
  const { sites } = await listSites();
  redirect(sites[0] ? `/sites/${sites[0].id}/articles` : "/sites");
}
