import { type NextRequest, NextResponse } from "next/server";
import * as client from "openid-client";

import {
  cookieOptions,
  FLOW_COOKIE,
  type Flow,
  oidc,
  safeReturnTo,
  seal,
  settings,
} from "@/lib/auth/session";

// Starts sign-in: sends the browser to Keycloak's login page.
export async function GET(request: NextRequest) {
  const config = await oidc();
  const flow: Flow = {
    verifier: client.randomPKCECodeVerifier(),
    state: client.randomState(),
    nonce: client.randomNonce(),
    returnTo: safeReturnTo(request.nextUrl.searchParams.get("returnTo")),
  };
  const url = client.buildAuthorizationUrl(config, {
    redirect_uri: `${settings().appUrl}/auth/callback`,
    scope: "openid profile email",
    code_challenge: await client.calculatePKCECodeChallenge(flow.verifier),
    code_challenge_method: "S256",
    state: flow.state,
    nonce: flow.nonce,
  });
  const response = NextResponse.redirect(url);
  response.cookies.set(FLOW_COOKIE, await seal(flow, 600), cookieOptions(600));
  return response;
}
