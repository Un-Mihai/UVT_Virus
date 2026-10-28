// Interface languages. Pure functions, shared by src/proxy.ts, Server and Client Components.

export const LOCALES = ["en", "ro"] as const;
export type Locale = (typeof LOCALES)[number];
const DEFAULT_LOCALE: Locale = "en";
/** Remembers the language someone last used; src/proxy.ts sets it. */
export const LOCALE_COOKIE = "app_locale";

/** Each language's name in its own language, for the switcher. */
export const LOCALE_NAMES: Record<Locale, string> = {
  en: "English",
  ro: "Română",
};

export function isLocale(value: string | undefined | null): value is Locale {
  return LOCALES.some((locale) => locale === value);
}

/** The best supported language for an Accept-Language header, or the default. */
export function negotiateLocale(acceptLanguage: string | null): Locale {
  const ranked = (acceptLanguage ?? "")
    .split(",")
    .map((entry) => {
      const [tag = "", ...params] = entry.split(";").map((part) => part.trim());
      const quality = params.find((param) => param.startsWith("q="));
      return {
        language: tag.toLowerCase().split("-")[0],
        weight: quality ? Number(quality.slice(2)) : 1,
      };
    })
    .filter(({ weight }) => weight > 0)
    .sort((a, b) => b.weight - a.weight);
  const match = ranked.find(({ language }) => isLocale(language));
  return match && isLocale(match.language) ? match.language : DEFAULT_LOCALE;
}

/** "/projects/3" in a language: "/ro/projects/3". */
export function withLocale(locale: Locale, path: string): string {
  return path === "/" ? `/${locale}` : `/${locale}${path}`;
}

/** The language prefix of a pathname and the rest: "/ro/projects/3" → ["ro", "/projects/3"]. */
export function splitLocale(pathname: string): [Locale | null, string] {
  const [, first, ...rest] = pathname.split("/");
  if (!isLocale(first)) return [null, pathname];
  return [first, `/${rest.join("/")}`];
}
