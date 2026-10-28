import { type NextRequest, NextResponse } from "next/server";
import * as client from "openid-client";

import {
  ACCESS_COOKIE,
  type Access,
  cookieOptions,
  oidc,
  type Session,
  SESSION_COOKIE,
  settings,
  tokenCookies,
  unseal,
} from "@/lib/auth/session";

// Every page and /api call needs a signed-in user. /auth/* runs the sign-in itself.
export async function proxy(request: NextRequest) {
  if (request.nextUrl.pathname.startsWith("/auth/")) return NextResponse.next();

  const session = await unseal<Session>(
    request.cookies.get(SESSION_COOKIE)?.value,
  );
  if (!session) return signIn(request);

  const access = await unseal<Access>(
    request.cookies.get(ACCESS_COOKIE)?.value,
  );
  if (access && access.expiresAt - Date.now() / 1000 > 30)
    return NextResponse.next();

  // The access token is gone or about to expire: refresh it and hand the new cookies to this
  // request too, so pages and the /api route see a valid token right away.
  let cookies;
  try {
    const tokens = await client.refreshTokenGrant(
      await oidc(),
      session.refreshToken,
    );
    cookies = await tokenCookies(tokens, session);
  } catch {
    return signIn(request); // the session ended in Keycloak
  }
  const jar = new Map(
    request.cookies.getAll().map(({ name, value }) => [name, value]),
  );
  for (const [name, value] of cookies) jar.set(name, value);
  const headers = new Headers(request.headers);
  headers.set(
    "cookie",
    [...jar].map(([name, value]) => `${name}=${value}`).join("; "),
  );
  const response = NextResponse.next({ request: { headers } });
  for (const [name, value, maxAge] of cookies) {
    response.cookies.set(name, value, cookieOptions(maxAge));
  }
  return response;
}

function signIn(request: NextRequest) {
  const response = request.nextUrl.pathname.startsWith("/api/")
    ? NextResponse.json({ detail: "Sign in required." }, { status: 401 })
    : NextResponse.redirect(loginUrl(request));
  response.cookies.delete(SESSION_COOKIE);
  response.cookies.delete(ACCESS_COOKIE);
  return response;
}

function loginUrl(request: NextRequest) {
  const url = new URL("/auth/login", settings().appUrl);
  url.searchParams.set(
    "returnTo",
    request.nextUrl.pathname + request.nextUrl.search,
  );
  return url;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|icon.svg|favicon.ico).*)"],
};
