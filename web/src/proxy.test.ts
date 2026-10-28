import { NextRequest } from "next/server";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { LOCALE_COOKIE } from "@/i18n/locales";

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
    new NextRequest("http://localhost:3000/en/status?tab=calls"),
  );

  expect(response.status).toBe(307);
  expect(response.headers.get("location")).toBe(
    "http://localhost:3000/auth/login?returnTo=%2Fen%2Fstatus%3Ftab%3Dcalls",
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
  const response = await proxy(await signedIn("/en/status"));

  expect(response.headers.get("x-middleware-next")).toBe("1");
});

it("does not trust a tampered session cookie", async () => {
  const request = new NextRequest("http://localhost:3000/en/status", {
    headers: { cookie: `${SESSION_COOKIE}=not-a-sealed-value` },
  });

  const response = await proxy(request);
  expect(response.status).toBe(307);
  expect(response.headers.get("location")).toMatch(
    /^http:\/\/localhost:3000\/auth\/login\?/,
  );
});

describe("languages", () => {
  async function redirectOf(
    path: string,
    headers: Record<string, string> = {},
  ) {
    const response = await proxy(
      new NextRequest(`http://localhost:3000${path}`, { headers }),
    );
    return response.headers.get("location");
  }

  it("adds the remembered language, then the browser's, then English", async () => {
    expect(
      await redirectOf("/projects/3?x=1", { cookie: `${LOCALE_COOKIE}=ro` }),
    ).toBe("http://localhost:3000/ro/projects/3?x=1");
    expect(
      await redirectOf("/projects/3", { "accept-language": "ro-RO,ro;q=0.9" }),
    ).toBe("http://localhost:3000/ro/projects/3");
    expect(await redirectOf("/projects/3", { "accept-language": "de" })).toBe(
      "http://localhost:3000/en/projects/3",
    );
  });

  it("sends the root to the language's start page", async () => {
    expect(await redirectOf("/")).toBe("http://localhost:3000/en");
  });

  it("never adds a language to API calls or files", async () => {
    const api = await proxy(new NextRequest("http://localhost:3000/api/me"));
    expect(api.status).toBe(401);
    // Files still need sign-in, but keep their address.
    expect(await redirectOf("/robots.txt")).toBe(
      "http://localhost:3000/auth/login?returnTo=%2Frobots.txt",
    );
  });

  it("remembers the language of the page someone opens", async () => {
    const response = await proxy(await signedIn("/ro/status"));

    expect(response.headers.get("x-middleware-next")).toBe("1");
    expect(response.cookies.get(LOCALE_COOKIE)?.value).toBe("ro");
  });
});
