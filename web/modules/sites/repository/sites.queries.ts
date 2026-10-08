import "server-only";

import { cache } from "react";

import { apiServer } from "@/lib/api-server";
import type { Schemas } from "@/lib/api/types";

export type SiteWithStats = Schemas["SiteSummary"];

/** Cached per request: the agency layout and the site guard both read it. */
export const listSites = cache(async (): Promise<Schemas["SitesOut"]> => {
  return (await apiServer()).get("/sites");
});
