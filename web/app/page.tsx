import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { LAST_SITE_COOKIE } from "@/lib/last-site";
import { listSites } from "@/modules/sites/data";

export default async function Page() {
  const [{ sites }, cookieStore] = await Promise.all([listSites(), cookies()]);
  const last = cookieStore.get(LAST_SITE_COOKIE)?.value;
  const site = sites.find((s) => s.id === last) ?? sites[0];
  redirect(site ? `/sites/${site.id}/articles` : "/sites");
}
