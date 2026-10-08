import "server-only";

import { apiServer } from "@/lib/api-server";
import type { Schemas } from "@/lib/api/types";

export type SiteWithStats = Schemas["SiteSummary"];

export async function listSites(): Promise<Schemas["SitesOut"]> {
  return (await apiServer()).get("/sites");
}
