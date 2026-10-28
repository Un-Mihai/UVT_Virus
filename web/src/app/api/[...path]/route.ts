import { cookies } from "next/headers";

import { ACCESS_COOKIE, type Access, unseal } from "@/lib/auth/session";

// Forwards browser requests for /api/* to FastAPI, so the API needs no public URL or CORS.
// API_URL is read per request, so one image works in every environment. The browser's cookies
// stay here: FastAPI only gets the signed-in user's access token.

const HOP_BY_HOP = [
  "connection",
  "host",
  "keep-alive",
  "transfer-encoding",
  "content-length",
];

async function forward(
  request: Request,
  context: RouteContext<"/api/[...path]">,
) {
  const { path } = await context.params;
  const api = new URL(process.env.API_URL ?? "http://localhost:8000");
  const target = new URL(`/api/${path.map(encodeURIComponent).join("/")}`, api);
  target.search = new URL(request.url).search;

  const headers = new Headers(request.headers);
  for (const name of [...HOP_BY_HOP, "cookie", "authorization"])
    headers.delete(name);
  const access = await unseal<Access>(
    (await cookies()).get(ACCESS_COOKIE)?.value,
  );
  if (access) headers.set("authorization", `Bearer ${access.accessToken}`);
  const hasBody = request.method !== "GET" && request.method !== "HEAD";

  // `duplex` is missing from the DOM typings but Node's fetch needs it to stream
  // a request body (file uploads).
  const init: RequestInit & { duplex?: "half" } = {
    method: request.method,
    headers,
    body: hasBody ? request.body : undefined,
    duplex: hasBody ? "half" : undefined,
    redirect: "manual",
    cache: "no-store",
  };
  const response = await fetch(target, init);

  const responseHeaders = new Headers(response.headers);
  for (const name of HOP_BY_HOP) responseHeaders.delete(name);
  responseHeaders.delete("content-encoding");
  // FastAPI's redirects (trailing slashes) name its internal address; keep them on this origin.
  const location = responseHeaders.get("location");
  if (location?.startsWith(api.origin)) {
    responseHeaders.set("location", location.slice(api.origin.length));
  }
  return new Response(response.body, {
    status: response.status,
    headers: responseHeaders,
  });
}

export {
  forward as DELETE,
  forward as GET,
  forward as PATCH,
  forward as POST,
  forward as PUT,
};
