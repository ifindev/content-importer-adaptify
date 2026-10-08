"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { apiUrl } from "@/lib/api-server";
import type { MutationResult } from "@/lib/mutation-result";

const SESSION_COOKIE_NAME = "session";
const EMAIL_COOKIE_NAME = "agency_email";
const SESSION_MAX_AGE = 60 * 60 * 24 * 5; // 5 days, matches T-012's SESSION_EXPIRES_IN

/**
 * Exchanges a Firebase ID token for the agency session cookie. The API's
 * Set-Cookie value is re-set here because the browser never calls FastAPI
 * directly (see architecture.md Auth).
 */
export async function createSession(
  idToken: string,
  email: string | null,
): Promise<MutationResult<null>> {
  const response = await fetch(`${apiUrl()}/auth/session`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id_token: idToken }),
  });

  if (!response.ok) {
    return { ok: false, code: "invalid_token" };
  }

  const setCookie = response.headers.get("set-cookie");
  const sessionValue = setCookie?.match(/session=([^;]+)/)?.[1];
  if (!sessionValue) {
    return { ok: false, code: "invalid_token" };
  }

  const cookieStore = await cookies();
  cookieStore.set(SESSION_COOKIE_NAME, sessionValue, {
    httpOnly: true,
    secure: process.env.APP_ENV !== "local",
    sameSite: "lax",
    path: "/",
    maxAge: SESSION_MAX_AGE,
  });
  if (email) {
    cookieStore.set(EMAIL_COOKIE_NAME, email, {
      httpOnly: false,
      secure: process.env.APP_ENV !== "local",
      sameSite: "lax",
      path: "/",
      maxAge: SESSION_MAX_AGE,
    });
  }

  return { ok: true, data: null };
}

export async function logout(): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.delete(SESSION_COOKIE_NAME);
  cookieStore.delete(EMAIL_COOKIE_NAME);
  redirect("/login");
}
