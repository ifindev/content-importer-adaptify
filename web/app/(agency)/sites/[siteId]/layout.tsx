import { notFound } from "next/navigation";

import type { PageProps } from "@/lib/types/page-props";
import { listSites } from "@/modules/sites/data";

/**
 * An unknown site 404s on every site route, including Import, which makes
 * no site-scoped read of its own. listSites is cached per request, so this
 * shares the agency layout's call.
 */
export default async function SiteLayout({
  children,
  params,
}: PageProps<{ siteId: string }> & { children: React.ReactNode }) {
  const { siteId } = await params;
  const { sites } = await listSites();
  if (!sites.some((s) => s.id === siteId)) notFound();
  return children;
}
