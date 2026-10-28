import { type NextRequest, NextResponse } from "next/server";
import * as client from "openid-client";

import {
  ACCESS_COOKIE,
  oidc,
  type Session,
  SESSION_COOKIE,
  settings,
  unseal,
} from "@/lib/auth/session";

// Ends the session here and in Keycloak, then comes back to the app (which asks to sign in).
export async function POST(request: NextRequest) {
  const { appUrl, clientId } = settings();
  const session = await unseal<Session>(
    request.cookies.get(SESSION_COOKIE)?.value,
  );
  const url = client.buildEndSessionUrl(await oidc(), {
    post_logout_redirect_uri: `${appUrl}/`,
    ...(session?.idToken
      ? { id_token_hint: session.idToken }
      : { client_id: clientId }),
  });
  const response = NextResponse.redirect(url, 303);
  response.cookies.delete(SESSION_COOKIE);
  response.cookies.delete(ACCESS_COOKIE);
  return response;
}
