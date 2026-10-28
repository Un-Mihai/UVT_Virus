"use client";

import { usePathname, useSearchParams } from "next/navigation";

import {
  LOCALE_NAMES,
  LOCALES,
  type Locale,
  splitLocale,
  withLocale,
} from "@/i18n/locales";

/** The same page in the other language. Plain links on purpose: a prefetch of the other
 *  language would pass through src/proxy.ts and switch the remembered language. */
export function LanguageSwitcher({
  locale,
  label,
}: {
  locale: Locale;
  label: string;
}) {
  const [, path] = splitLocale(usePathname());
  const query = useSearchParams().toString();
  const search = query ? `?${query}` : "";

  return (
    <nav aria-label={label} className="flex items-center gap-1">
      {LOCALES.map((option) =>
        option === locale ? (
          <span
            key={option}
            aria-current="page"
            lang={option}
            className="rounded-md bg-surface-2 px-2.5 py-1.5 font-medium text-ink"
          >
            {LOCALE_NAMES[option]}
          </span>
        ) : (
          <a
            key={option}
            href={withLocale(option, path) + search}
            hrefLang={option}
            lang={option}
            className="rounded-md px-2.5 py-1.5 font-medium text-ink-2 transition-colors duration-150 hover:bg-surface-2 hover:text-ink"
          >
            {LOCALE_NAMES[option]}
          </a>
        ),
      )}
    </nav>
  );
}
