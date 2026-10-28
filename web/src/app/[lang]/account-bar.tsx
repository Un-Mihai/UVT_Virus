import Link from "next/link";

import { quietButton } from "@/components/styles";
import { currentLocale, getDictionary } from "@/i18n/dictionary";
import { withLocale } from "@/i18n/locales";
import { currentUser } from "@/lib/auth/current-user";
import { hasRole, type Role } from "@/lib/roles";

import { LanguageSwitcher } from "./language-switcher";

const navLink =
  "inline-flex min-h-10 items-center rounded-control px-3 py-2 font-medium text-ink-2 transition-colors duration-150 hover:bg-surface-2 hover:text-ink";

/** The app's name, where each role works, the language, who is signed in, and the way out. */
export async function AccountBar() {
  const user = await currentUser();
  if (!user) return null;
  const [dictionary, locale] = await Promise.all([
    getDictionary(),
    currentLocale(),
  ]);
  const roles = (["client", "reviewer", "admin"] as const satisfies Role[])
    .filter((role) => hasRole(user, role))
    .map((role) => dictionary.roles[role]);

  return (
    <div className="account-bar">
      <div className="mx-auto flex min-h-20 w-full max-w-360 flex-wrap items-center gap-x-6 gap-y-3 px-5 py-4 text-sm sm:px-10">
        <nav
          aria-label={dictionary.nav.label}
          className="flex flex-wrap items-center gap-x-1 gap-y-2"
        >
          <Link
            href={withLocale(locale, "/")}
            className="brand-link mr-4 inline-flex min-h-10 items-center gap-3 rounded-control py-1 text-base font-bold tracking-tight text-ink"
          >
            {dictionary.app.name}
          </Link>
          {hasRole(user, "admin") && (
            <Link
              href={withLocale(locale, "/admin/regulations")}
              className={navLink}
            >
              {dictionary.nav.regulations}
            </Link>
          )}
          <Link href={withLocale(locale, "/status")} className={navLink}>
            {dictionary.nav.status}
          </Link>
        </nav>
        <div className="flex w-full flex-wrap items-center gap-x-4 gap-y-2 sm:ml-auto sm:w-auto">
          <LanguageSwitcher locale={locale} label={dictionary.nav.language} />
          <span className="min-w-0 wrap-anywhere text-ink-2">
            <span className="font-medium text-ink">
              {user.name ?? user.username}
            </span>
            {roles.length > 0 && <> · {roles.join(", ")}</>}
          </span>
          <form action="/auth/logout" method="post">
            <button type="submit" className={quietButton}>
              {dictionary.nav.signOut}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
