import "server-only";

import { notFound } from "next/navigation";

import { apiServer } from "@/lib/api-server";
import type { Schemas } from "@/lib/api/types";
import { orNotFound } from "@/lib/mutation-result";

export async function getReport(siteId: string): Promise<Schemas["ReportOut"]> {
  return orNotFound((await apiServer()).get(`/sites/${siteId}/report`), notFound);
}
