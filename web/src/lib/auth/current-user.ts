import "server-only";

import { cookies } from "next/headers";

import { type Session, SESSION_COOKIE, unseal } from "./session";

export type CurrentUser = Session["user"];

/** The signed-in user from the session cookie; src/proxy.ts lets no page render without one. */
export async function currentUser(): Promise<CurrentUser | null> {
  const session = await unseal<Session>(
    (await cookies()).get(SESSION_COOKIE)?.value,
  );
  return session?.user ?? null;
}
