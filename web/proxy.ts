import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const AGENCY_PATHS = ["/", "/import", "/articles", "/report"];

function isAgencyPath(pathname: string): boolean {
  return AGENCY_PATHS.some(
    (path) => pathname === path || pathname.startsWith(`${path}/`),
  );
}

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const hasSession = request.cookies.has("session");

  if (pathname === "/login") {
    if (hasSession) {
      return NextResponse.redirect(new URL("/articles", request.url));
    }
    return NextResponse.next();
  }

  if (isAgencyPath(pathname)) {
    if (!hasSession) {
      const loginUrl = new URL("/login", request.url);
      loginUrl.searchParams.set("next", pathname);
      return NextResponse.redirect(loginUrl);
    }
    if (pathname === "/") {
      return NextResponse.redirect(new URL("/articles", request.url));
    }
  }

  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-pathname", pathname);
  return NextResponse.next({ request: { headers: requestHeaders } });
}

export const config = {
  matcher: ["/", "/import", "/articles/:path*", "/report", "/login"],
};
