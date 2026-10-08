import "server-only";

import { cookies, headers } from "next/headers";
import { redirect } from "next/navigation";

import { ApiError, HttpClient } from "@/lib/http";

/**
 * Read on use, not at module load: `next build` loads this module while
 * collecting page data, and the image is built without runtime env.
 */
export function apiUrl(): string {
  const url = process.env.API_URL;
  if (!url) {
    throw new Error("API_URL environment variable is required");
  }
  return url;
}

const CLIENT_METHODS = ["get", "post", "patch", "delete", "postForm"] as const;

/**
 * A 401 means the session cookie is missing, expired, revoked, or tampered.
 * This is the real auth check (proxy.ts only checks the cookie is present),
 * so any agency call that hits it redirects to /login with `expired=1`, which
 * tells proxy.ts to drop the dead cookie and the login page to say so.
 * `x-pathname` comes from proxy.ts, which runs on every agency route.
 */
async function redirectToLogin(): Promise<never> {
  const pathname = (await headers()).get("x-pathname") ?? "/";
  redirect(`/login?next=${encodeURIComponent(pathname)}&expired=1`);
}

/** Shared with the API, which trusts X-Client-IP only alongside it. */
const INTERNAL_API_SECRET = process.env.INTERNAL_API_SECRET ?? "";

/**
 * The client's address for the API's per-client rate limit. Next only sets
 * x-forwarded-for when it's missing, so a client can send its own; the last
 * entry is the one the nearest proxy appended (or Next's socket address).
 * ponytail: assumes exactly one proxy in front (nginx on the VPS); another hop
 * (a CDN) would need a different entry.
 */
function clientIp(forwardedFor: string | null): string {
  return forwardedFor?.split(",").at(-1)?.trim() ?? "";
}

export async function apiServer(): Promise<HttpClient> {
  const [cookieStore, headerList] = await Promise.all([cookies(), headers()]);
  const session = cookieStore.get("session")?.value;
  const ip = clientIp(headerList.get("x-forwarded-for"));

  const client = new HttpClient(apiUrl(), () => ({
    ...(session ? { Cookie: `session=${session}` } : {}),
    ...(ip && INTERNAL_API_SECRET
      ? { "X-Client-IP": ip, "X-Internal-Secret": INTERNAL_API_SECRET }
      : {}),
  }));

  return new Proxy(client, {
    get(target, prop, receiver) {
      const value = Reflect.get(target, prop, receiver);
      if (
        typeof value !== "function" ||
        !CLIENT_METHODS.includes(prop as (typeof CLIENT_METHODS)[number])
      ) {
        return value;
      }
      return async (...args: unknown[]) => {
        try {
          return await (value as (...a: unknown[]) => unknown).apply(
            target,
            args,
          );
        } catch (error) {
          if (error instanceof ApiError && error.status === 401) {
            return redirectToLogin();
          }
          throw error;
        }
      };
    },
  });
}
