import "server-only";

import { cookies, headers } from "next/headers";

import { HttpClient } from "@/lib/http";

const API_URL: string = (() => {
  const url = process.env.API_URL;
  if (!url) {
    throw new Error("API_URL environment variable is required");
  }
  return url;
})();

export async function apiServer(): Promise<HttpClient> {
  const [cookieStore, headerList] = await Promise.all([cookies(), headers()]);
  const session = cookieStore.get("session")?.value;
  const forwardedFor = headerList.get("x-forwarded-for") ?? "";

  return new HttpClient(API_URL, () => ({
    ...(session ? { Cookie: `session=${session}` } : {}),
    "X-Forwarded-For": forwardedFor,
  }));
}
