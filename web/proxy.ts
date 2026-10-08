import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import { LAST_SITE_COOKIE, siteIdFromPath } from "@/lib/last-site";

const AGENCY_HOME = "/app";

function isAgencyPath(pathname: string): boolean {
  return (
    pathname === AGENCY_HOME ||
    pathname === "/sites" ||
    pathname.startsWith("/sites/")
  );
}

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const hasSession = request.cookies.has("session");

  if (pathname === "/login") {
    // The API rejected this cookie (apiServer's 401 redirect). Drop it, or
    // the hasSession check below would bounce back to the app and loop.
    if (request.nextUrl.searchParams.get("expired") === "1") {
      const response = NextResponse.next();
      response.cookies.delete("session");
      return response;
    }
    if (hasSession) {
      return NextResponse.redirect(new URL(AGENCY_HOME, request.url));
    }
    return NextResponse.next();
  }

  // "/" is the public landing page; a signed-in agency goes straight to the app.
  if (pathname === "/") {
    return hasSession
      ? NextResponse.redirect(new URL(AGENCY_HOME, request.url))
      : NextResponse.next();
  }

  if (isAgencyPath(pathname) && !hasSession) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-pathname", pathname);
  const response = NextResponse.next({ request: { headers: requestHeaders } });
  // Remembered so /app reopens the last site and the Sites list marks it.
  const siteId = siteIdFromPath(pathname);
  if (siteId && request.cookies.get(LAST_SITE_COOKIE)?.value !== siteId) {
    response.cookies.set(LAST_SITE_COOKIE, siteId, {
      httpOnly: true,
      sameSite: "lax",
      path: "/",
      maxAge: 60 * 60 * 24 * 365,
    });
  }
  return response;
}

export const config = {
  matcher: ["/", "/app", "/sites/:path*", "/login"],
};
