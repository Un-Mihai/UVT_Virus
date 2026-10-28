import { type NextRequest, NextResponse } from "next/server";
import * as client from "openid-client";

import {
  cookieOptions,
  FLOW_COOKIE,
  type Flow,
  oidc,
  settings,
  tokenCookies,
  unseal,
} from "@/lib/auth/session";

// Keycloak sends the browser back here with a one-time code; trade it for tokens.
export async function GET(request: NextRequest) {
  const { appUrl } = settings();
  const flow = await unseal<Flow>(request.cookies.get(FLOW_COOKIE)?.value);
  if (!flow) return NextResponse.redirect(new URL("/auth/login", appUrl));

  let tokens: client.TokenEndpointResponse;
  try {
    // Built from APP_URL: behind a proxy, request.url is the container's own address.
    const callback = new URL(`/auth/callback${request.nextUrl.search}`, appUrl);
    tokens = await client.authorizationCodeGrant(await oidc(), callback, {
      pkceCodeVerifier: flow.verifier,
      expectedState: flow.state,
      expectedNonce: flow.nonce,
    });
  } catch (error) {
    const reason = error instanceof Error ? error.message : "unknown error";
    return new Response(
      `Sign-in failed: ${reason}\n\nStart again at ${appUrl}/auth/login`,
      { status: 400, headers: { "content-type": "text/plain; charset=utf-8" } },
    );
  }

  const response = NextResponse.redirect(new URL(flow.returnTo, appUrl));
  for (const [name, value, maxAge] of await tokenCookies(tokens)) {
    response.cookies.set(name, value, cookieOptions(maxAge));
  }
  response.cookies.delete(FLOW_COOKIE);
  return response;
}
