import { notFound } from "next/navigation";
import { lang } from "next/root-params";

import { type Dictionary, en } from "./dictionaries/en";
import { ro } from "./dictionaries/ro";
import { isLocale, type Locale } from "./locales";

const DICTIONARIES: Record<Locale, Dictionary> = { en, ro };

/** The page's language, from the /{lang} segment. Server Components only. */
export async function currentLocale(): Promise<Locale> {
  const locale = await lang();
  if (!isLocale(locale)) notFound();
  return locale;
}

/** All interface strings in the page's language. Pass slices to Client Components as props. */
export async function getDictionary(): Promise<Dictionary> {
  return DICTIONARIES[await currentLocale()];
}
