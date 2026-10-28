import createClient from "openapi-fetch";

import type { paths } from "./schema";

/** Typed FastAPI client for Client Components; requests go through the /api proxy route. */
export const api = createClient<paths>({ baseUrl: "" });
