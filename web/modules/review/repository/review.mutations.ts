"use server";

import { revalidatePath } from "next/cache";

import { apiServer } from "@/lib/api-server";
import type { Schemas } from "@/lib/api/types";
import { toResult, type MutationResult } from "@/lib/mutation-result";

async function decide(
  token: string,
  path: string,
  body: Schemas["ApproveRequest"] | Schemas["RequestChangesRequest"],
): Promise<MutationResult<Schemas["ReviewActionOut"]>> {
  const result = await toResult(
    (await apiServer()).post<Schemas["ReviewActionOut"]>(path, body),
  );
  if (result.ok) {
    revalidatePath(`/review/${token}`, "layout");
    // The token doesn't say which site; refresh every agency view.
    revalidatePath("/sites", "layout");
  }
  return result;
}

export async function approve(
  token: string,
  id: string,
  form: Schemas["ApproveRequest"],
) {
  return decide(token, `/review/${token}/articles/${id}/approve`, form);
}

export async function requestChanges(
  token: string,
  id: string,
  form: Schemas["RequestChangesRequest"],
) {
  return decide(token, `/review/${token}/articles/${id}/request-changes`, form);
}
