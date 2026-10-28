import { afterEach, expect, it, vi } from "vitest";

// Route handlers read cookies through next/headers, which needs a request scope.
vi.mock("next/headers", () => ({
  cookies: async () => ({ get: () => undefined }),
}));

import { POST } from "./route";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

it("forwards method, path, query and body to API_URL without hop-by-hop headers", async () => {
  const upstream = vi.fn<typeof fetch>(
    async () =>
      new Response('{"ok":true}', {
        status: 201,
        headers: {
          "content-type": "application/json",
          "content-encoding": "gzip",
        },
      }),
  );
  vi.stubGlobal("fetch", upstream);
  vi.stubEnv("API_URL", "http://api:8000");

  const request = new Request(
    "http://localhost:3000/api/documents/a%20b?page=2",
    {
      method: "POST",
      body: "file-bytes",
      headers: { host: "localhost:3000", "x-team": "blue" },
    },
  );
  const response = await POST(request, {
    params: Promise.resolve({ path: ["documents", "a b"] }),
  });

  const [target, init] = upstream.mock.calls[0];
  const sent = new Headers(init?.headers);
  expect(String(target)).toBe("http://api:8000/api/documents/a%20b?page=2");
  expect(init?.method).toBe("POST");
  expect(sent.get("host")).toBeNull();
  expect(sent.get("x-team")).toBe("blue");
  expect(response.status).toBe(201);
  // Node's fetch already decompressed the body, so the encoding header must not reach the browser.
  expect(response.headers.get("content-encoding")).toBeNull();
  expect(await response.json()).toEqual({ ok: true });
});

it("keeps FastAPI's redirects on this origin", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn<typeof fetch>(
      async () =>
        new Response(null, {
          status: 307,
          headers: { location: "http://api:8000/api/ai/usage" },
        }),
    ),
  );
  vi.stubEnv("API_URL", "http://api:8000");

  const response = await POST(
    new Request("http://localhost:3000/api/ai/usage/", { method: "POST" }),
    { params: Promise.resolve({ path: ["ai", "usage", ""] }) },
  );

  expect(response.status).toBe(307);
  expect(response.headers.get("location")).toBe("/api/ai/usage");
});
