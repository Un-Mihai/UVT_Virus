import "server-only";

import { cookies } from "next/headers";
import createClient from "openapi-fetch";

import { ACCESS_COOKIE, type Access, unseal } from "@/lib/auth/session";

import type { paths } from "./schema";

/** Typed FastAPI client for Server Components, Server Actions and Route Handlers. */
export const api = createClient<paths>({
  baseUrl: process.env.API_URL ?? "http://localhost:8000",
  // Every call carries the signed-in user's access token (src/proxy.ts keeps it fresh). A custom
  // fetch rather than middleware: openapi-fetch middleware calls Math.random(), which Cache
  // Components refuses before request-time data is read.
  fetch: async (request: Request) => {
    const access = await unseal<Access>(
      (await cookies()).get(ACCESS_COOKIE)?.value,
    );
    if (access) {
      request.headers.set("Authorization", `Bearer ${access.accessToken}`);
    }
    return fetch(request);
  },
});
