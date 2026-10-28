import { cookies } from "next/headers";

import { type Session, SESSION_COOKIE, unseal } from "@/lib/auth/session";

/** Who is signed in, and the way out. Pages only render for signed-in users (src/proxy.ts). */
export async function AccountBar() {
  const session = await unseal<Session>(
    (await cookies()).get(SESSION_COOKIE)?.value,
  );
  if (!session) return null;
  const { user } = session;

  return (
    <div className="border-b border-line">
      <div className="mx-auto flex w-full max-w-5xl items-center justify-end gap-3 px-5 py-2 text-sm sm:px-10">
        <span className="text-ink-2">
          <span className="font-medium text-ink">
            {user.name ?? user.username}
          </span>
          {user.roles.length > 0 && <> · {user.roles.join(", ")}</>}
        </span>
        <form action="/auth/logout" method="post">
          <button
            type="submit"
            className="rounded-md px-2.5 py-1.5 font-medium text-ink-2 transition-colors duration-150 hover:bg-surface-2 hover:text-ink"
          >
            Sign out
          </button>
        </form>
      </div>
    </div>
  );
}
