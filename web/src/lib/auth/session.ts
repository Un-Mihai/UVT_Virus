// Sign-in with Keycloak (OpenID Connect, authorization code + PKCE). This server is the only
// OIDC client: tokens live in encrypted httpOnly cookies and never reach browser JavaScript.
import { createHash } from "node:crypto";

import { decodeJwt, EncryptJWT, jwtDecrypt } from "jose";
import * as client from "openid-client";

export const SESSION_COOKIE = "app_session";
export const ACCESS_COOKIE = "app_access";
export const FLOW_COOKIE = "app_auth_flow";

type User = {
  id: string;
  username: string;
  name?: string;
  email?: string;
  roles: string[];
};
/** Long-lived: who is signed in and how to get new access tokens. */
export type Session = { user: User; refreshToken: string; idToken?: string };
/** Short-lived: what the API accepts. Split from Session to stay under the 4 KB cookie limit. */
export type Access = { accessToken: string; expiresAt: number };
/** In flight between /auth/login and /auth/callback. */
export type Flow = {
  verifier: string;
  state: string;
  nonce: string;
  returnTo: string;
};

type Cookie = [name: string, value: string, maxAge: number];

export function settings() {
  return {
    appUrl: process.env.APP_URL ?? "http://localhost:3000",
    issuer: process.env.AUTH_ISSUER ?? "http://localhost:8080/realms/app",
    // Inside Docker the issuer's public address is not reachable from this server.
    internalUrl: process.env.AUTH_INTERNAL_URL,
    clientId: process.env.AUTH_CLIENT_ID ?? "web",
    clientSecret: process.env.AUTH_CLIENT_SECRET ?? "local-web-client-secret",
  };
}

let configuration: Promise<client.Configuration> | undefined;

/** Keycloak's endpoints, discovered once per server process. */
export function oidc(): Promise<client.Configuration> {
  configuration ??= discover().catch((error: unknown) => {
    configuration = undefined;
    throw error;
  });
  return configuration;
}

async function discover(): Promise<client.Configuration> {
  const { issuer, internalUrl, clientId, clientSecret } = settings();
  const options: client.DiscoveryRequestOptions = {};
  if (internalUrl) {
    const publicOrigin = new URL(issuer).origin;
    // Same Fetch API; openid-client's option types are wider than the DOM's RequestInit.
    options[client.customFetch] = (url, init) =>
      fetch(url.replace(publicOrigin, internalUrl), init as RequestInit);
  }
  if (issuer.startsWith("http://"))
    options.execute = [client.allowInsecureRequests];
  return client.discovery(
    new URL(issuer),
    clientId,
    clientSecret,
    undefined,
    options,
  );
}

function key(): Uint8Array {
  const secret =
    process.env.AUTH_SECRET ??
    (process.env.NODE_ENV === "production"
      ? undefined
      : "local-development-only-secret-change-me");
  if (!secret) throw new Error("Set AUTH_SECRET to sign users in.");
  return createHash("sha256").update(secret).digest();
}

export async function seal(value: object, maxAge: number): Promise<string> {
  return new EncryptJWT({ value })
    .setProtectedHeader({ alg: "dir", enc: "A256GCM" })
    .setExpirationTime(`${maxAge}s`)
    .encrypt(key());
}

/** The cookie's content, or null when it is missing, tampered with or expired. */
export async function unseal<T>(sealed: string | undefined): Promise<T | null> {
  if (!sealed) return null;
  try {
    const { payload } = await jwtDecrypt(sealed, key());
    return payload.value as T;
  } catch {
    return null;
  }
}

export function cookieOptions(maxAge: number) {
  return {
    httpOnly: true,
    sameSite: "lax" as const,
    secure: settings().appUrl.startsWith("https://"),
    path: "/",
    maxAge,
  };
}

/** Session and access cookies for a token endpoint response (sign-in or refresh). */
export async function tokenCookies(
  tokens: client.TokenEndpointResponse,
  previous?: Session,
): Promise<Cookie[]> {
  const claims = decodeJwt(tokens.access_token);
  const realmAccess = claims.realm_access as { roles?: string[] } | undefined;
  const user: User = {
    id: String(claims.sub),
    username: String(claims.preferred_username ?? claims.sub),
    name: claims.name as string | undefined,
    email: claims.email as string | undefined,
    roles: realmAccess?.roles ?? [],
  };
  const refreshToken = tokens.refresh_token ?? previous?.refreshToken;
  if (!refreshToken) throw new Error("Keycloak returned no refresh token.");
  const accessAge = tokens.expires_in ?? 300;
  const sessionAge = Number(tokens.refresh_expires_in ?? 36_000);
  const session: Session = {
    user,
    refreshToken,
    idToken: tokens.id_token ?? previous?.idToken,
  };
  const access: Access = {
    accessToken: tokens.access_token,
    expiresAt: Math.floor(Date.now() / 1000) + accessAge,
  };
  return [
    [SESSION_COOKIE, await seal(session, sessionAge), sessionAge],
    [ACCESS_COOKIE, await seal(access, accessAge), accessAge],
  ];
}

/** Only paths on this app, so the login link cannot send people elsewhere. */
export function safeReturnTo(path: string | null): string {
  const app = new URL(settings().appUrl);
  try {
    // Resolved the way the browser will: "/\evil.example" is another site.
    const url = new URL(path ?? "/", app);
    if (url.origin === app.origin) return url.pathname + url.search;
  } catch {
    // not a URL at all
  }
  return "/";
}
