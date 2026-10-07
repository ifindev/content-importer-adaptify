import "server-only";

import { cookies, headers } from "next/headers";
import { redirect } from "next/navigation";

import { ApiError, HttpClient } from "@/lib/http";

const API_URL: string = (() => {
  const url = process.env.API_URL;
  if (!url) {
    throw new Error("API_URL environment variable is required");
  }
  return url;
})();

const CLIENT_METHODS = ["get", "post", "patch", "delete", "postForm"] as const;

/**
 * A 401 means the session cookie is missing, expired, revoked, or tampered.
 * This is the real auth check (proxy.ts only checks the cookie is present),
 * so any agency call that hits it redirects to /login, same as a logged-out
 * visit. `x-pathname` comes from proxy.ts, which runs on every agency route.
 */
async function redirectToLogin(): Promise<never> {
  const pathname = (await headers()).get("x-pathname") ?? "/";
  redirect(`/login?next=${encodeURIComponent(pathname)}`);
}

export async function apiServer(): Promise<HttpClient> {
  const [cookieStore, headerList] = await Promise.all([cookies(), headers()]);
  const session = cookieStore.get("session")?.value;
  const forwardedFor = headerList.get("x-forwarded-for") ?? "";

  const client = new HttpClient(API_URL, () => ({
    ...(session ? { Cookie: `session=${session}` } : {}),
    "X-Forwarded-For": forwardedFor,
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
