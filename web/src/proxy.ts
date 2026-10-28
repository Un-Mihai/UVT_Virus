import { type NextRequest, NextResponse } from "next/server";
import * as client from "openid-client";

import {
  isLocale,
  LOCALE_COOKIE,
  negotiateLocale,
  splitLocale,
  withLocale,
} from "@/i18n/locales";
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

const ONE_YEAR = 60 * 60 * 24 * 365;

// Pages live under /{language}; every page and /api call needs a signed-in user. /auth/* runs
// the sign-in itself.
export async function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  if (pathname.startsWith("/auth/")) return NextResponse.next();
  if (needsLanguage(pathname))
    return NextResponse.redirect(languageUrl(request));

  const response = await signedIn(request);
  const [locale] = splitLocale(pathname);
  if (locale && request.cookies.get(LOCALE_COOKIE)?.value !== locale) {
    response.cookies.set(LOCALE_COOKIE, locale, cookieOptions(ONE_YEAR));
  }
  return response;
}

/** A page address without a language prefix; /api and files (anything with a dot) have none. */
function needsLanguage(pathname: string) {
  if (pathname.startsWith("/api/")) return false;
  if (pathname.split("/").at(-1)?.includes(".")) return false;
  return splitLocale(pathname)[0] === null;
}

/** The same address in the remembered language, else the browser's, else English. */
function languageUrl(request: NextRequest) {
  const remembered = request.cookies.get(LOCALE_COOKIE)?.value;
  const locale = isLocale(remembered)
    ? remembered
    : negotiateLocale(request.headers.get("accept-language"));
  const url = new URL(
    withLocale(locale, request.nextUrl.pathname),
    settings().appUrl,
  );
  url.search = request.nextUrl.search;
  return url;
}

async function signedIn(request: NextRequest) {
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
