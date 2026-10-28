import type { Locale } from "./locales";

/** Fills {name} placeholders: fill("Page {page}", { page: 3 }) → "Page 3". */
export function fill(
  template: string,
  values: Record<string, string | number>,
): string {
  return template.replace(/\{(\w+)\}/g, (placeholder, name: string) =>
    name in values ? String(values[name]) : placeholder,
  );
}

/** Plural forms by Intl category; Romanian also has "few" (2–19 and 0 take no "de"). */
export type PluralForms = { one: string; other: string; few?: string };

/** The right form for a count, with {count} filled in. */
export function plural(
  locale: Locale,
  count: number,
  forms: PluralForms,
): string {
  const category = new Intl.PluralRules(locale).select(count);
  const form =
    category === "one"
      ? forms.one
      : category === "few"
        ? (forms.few ?? forms.other)
        : forms.other;
  return fill(form, { count });
}
