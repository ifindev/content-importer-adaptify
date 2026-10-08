"use server";

import { revalidatePath } from "next/cache";

import { apiServer } from "@/lib/api-server";
import type { Schemas } from "@/lib/api/types";
import { toResult, type MutationResult } from "@/lib/mutation-result";

export async function createSite(
  form: Schemas["SiteCreate"],
): Promise<MutationResult<Schemas["SiteOut"]>> {
  const result = await toResult(
    (await apiServer()).post<Schemas["SiteOut"]>("/sites", form),
  );
  if (result.ok) revalidatePath("/sites", "layout");
  return result;
}

/**
 * Without `siteId`, tests new credentials (Add Site). With it, tests the
 * stored credentials, `form` overriding any field given (an empty password
 * means the stored one).
 */
export async function testConnection(
  form: Partial<Schemas["SiteConnectionTest"]>,
  siteId?: string,
): Promise<MutationResult<null>> {
  const api = await apiServer();
  const result = await toResult(
    siteId
      ? api.post<null>(`/sites/${siteId}/test-connection`, form)
      : api.post<null>("/sites/test-connection", form),
  );
  if (siteId) revalidatePath("/sites", "layout");
  return result;
}

/** An empty password keeps the stored one. */
export async function updateSite(
  siteId: string,
  form: Schemas["SiteUpdate"],
): Promise<MutationResult<Schemas["SiteOut"]>> {
  const result = await toResult(
    (await apiServer()).patch<Schemas["SiteOut"]>(`/sites/${siteId}`, form),
  );
  if (result.ok) revalidatePath("/sites", "layout");
  return result;
}

/** Removes the site, its articles and its review link. */
export async function deleteSite(
  siteId: string,
): Promise<MutationResult<null>> {
  const result = await toResult(
    (await apiServer()).delete<null>(`/sites/${siteId}`),
  );
  if (result.ok) revalidatePath("/", "layout");
  return result;
}
