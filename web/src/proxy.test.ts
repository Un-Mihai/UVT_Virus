import { NextRequest } from "next/server";
import { afterEach, beforeEach, expect, it, vi } from "vitest";

import {
  ACCESS_COOKIE,
  type Access,
  seal,
  type Session,
  SESSION_COOKIE,
} from "@/lib/auth/session";

import { proxy } from "./proxy";

beforeEach(() => vi.stubEnv("APP_URL", "http://localhost:3000"));
afterEach(() => vi.unstubAllEnvs());

const user = { id: "user-1", username: "reviewer", roles: ["reviewer"] };

async function signedIn(path: string) {
  const session: Session = { user, refreshToken: "refresh" };
  const access: Access = {
    accessToken: "access",
    expiresAt: Math.floor(Date.now() / 1000) + 600,
  };
  const cookie = `${SESSION_COOKIE}=${await seal(session, 600)}; ${ACCESS_COOKIE}=${await seal(access, 600)}`;
  return new NextRequest(`http://localhost:3000${path}`, {
    headers: { cookie },
  });
}

it("sends people who are not signed in to the login, keeping where they were going", async () => {
  const response = await proxy(
    new NextRequest("http://localhost:3000/status?tab=calls"),
  );

  expect(response.status).toBe(307);
  expect(response.headers.get("location")).toBe(
    "http://localhost:3000/auth/login?returnTo=%2Fstatus%3Ftab%3Dcalls",
  );
});

it("answers API calls without a session with 401 instead of a redirect", async () => {
  const response = await proxy(
    new NextRequest("http://localhost:3000/api/ai/check", { method: "POST" }),
  );

  expect(response.status).toBe(401);
  expect(await response.json()).toEqual({ detail: "Sign in required." });
});

it("lets the sign-in routes through", async () => {
  const response = await proxy(
    new NextRequest("http://localhost:3000/auth/callback?code=x"),
  );

  expect(response.headers.get("x-middleware-next")).toBe("1");
});

it("lets signed-in requests through without calling Keycloak", async () => {
  const response = await proxy(await signedIn("/status"));

  expect(response.headers.get("x-middleware-next")).toBe("1");
});

it("does not trust a tampered session cookie", async () => {
  const request = new NextRequest("http://localhost:3000/status", {
    headers: { cookie: `${SESSION_COOKIE}=not-a-sealed-value` },
  });

  expect((await proxy(request)).status).toBe(307);
});
