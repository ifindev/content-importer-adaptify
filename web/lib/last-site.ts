/** The site the agency last opened, set by proxy.ts on `/sites/{id}/...`. */
export const LAST_SITE_COOKIE = "last_site";

/** `/sites/{id}/...` → `{id}`; anything else → null. */
export function siteIdFromPath(pathname: string): string | null {
  return pathname.match(/^\/sites\/([^/]+)\//)?.[1] ?? null;
}
