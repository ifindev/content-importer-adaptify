"use server";

import { revalidatePath } from "next/cache";

import type { Schemas } from "@/lib/api/types";
import { mutationFailure } from "@/lib/fixtures/scenario";
import { db, now } from "@/lib/fixtures/store";
import type { MutationResult } from "@/lib/mutation-result";

type SiteCreate = Schemas["SiteCreate"];

export async function createSite(
  form: SiteCreate,
): Promise<MutationResult<Schemas["SiteOut"]>> {
  const failure = await mutationFailure();
  if (failure) return failure;
  const id = form.name.toLowerCase().replace(/[^a-z0-9]+/g, "-") || "site";
  const site = {
    id: db.sites.some((s) => s.id === id) ? `${id}-${db.sites.length}` : id,
    name: form.name,
    wp_base_url: form.wp_base_url,
    wp_username: form.wp_username,
    connection_ok: true,
    connection_checked_at: now(),
  };
  db.sites.push(site);
  db.articles[site.id] = [];
  revalidatePath("/sites", "layout");
  return {
    ok: true,
    data: { id: site.id, name: site.name, wp_base_url: site.wp_base_url },
  };
}

/** Fixture-only: no API endpoint yet (see T-031's design follow-ups). */
export async function testConnection(
  form: Omit<SiteCreate, "name">,
): Promise<MutationResult<null>> {
  const failure = await mutationFailure();
  if (failure) return failure;
  void form;
  return { ok: true, data: null };
}

const toOut = (site: { id: string; name: string; wp_base_url: string }) => ({
  id: site.id,
  name: site.name,
  wp_base_url: site.wp_base_url,
});

/** T-035. An empty password keeps the stored one. */
export async function updateSite(
  siteId: string,
  form: Partial<SiteCreate>,
): Promise<MutationResult<Schemas["SiteOut"]>> {
  const failure = await mutationFailure();
  if (failure) return failure;
  const site = db.sites.find((s) => s.id === siteId);
  if (!site) return { ok: false, code: "site_not_found" };
  const changes = Object.fromEntries(
    Object.entries(form).filter(([, value]) => value),
  ) as Partial<SiteCreate>;
  if (Object.keys(changes).length === 0)
    return { ok: false, code: "empty_update" };
  Object.assign(site, {
    name: changes.name ?? site.name,
    wp_base_url: changes.wp_base_url ?? site.wp_base_url,
    wp_username: changes.wp_username ?? site.wp_username,
  });
  if (changes.wp_base_url || changes.wp_username || changes.wp_app_password) {
    site.connection_ok = true;
    site.connection_checked_at = now();
  }
  revalidatePath("/sites", "layout");
  return { ok: true, data: toOut(site) };
}

/** T-035. Removes the site, its articles and its review link. */
export async function deleteSite(
  siteId: string,
): Promise<MutationResult<null>> {
  const failure = await mutationFailure();
  if (failure) return failure;
  const index = db.sites.findIndex((s) => s.id === siteId);
  if (index === -1) return { ok: false, code: "site_not_found" };
  db.sites.splice(index, 1);
  delete db.articles[siteId];
  for (const [token, site] of Object.entries(db.reviewTokens)) {
    if (site === siteId) delete db.reviewTokens[token];
  }
  revalidatePath("/", "layout");
  return { ok: true, data: null };
}
