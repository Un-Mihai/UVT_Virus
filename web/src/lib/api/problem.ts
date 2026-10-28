import type { Dictionary } from "@/i18n/dictionaries/en";
import type { Locale } from "@/i18n/locales";
import { fill } from "@/i18n/template";

type Errors = Dictionary["errors"];

/** What an API answer that failed means, in the reader's language.
 *
 *  English pages show the API's own sentence, which names the problem and the fix. Romanian
 *  pages cannot (the API writes English), so they show `specific[status]` for the action, or
 *  the generic sentence for the status.
 */
export function problemText(
  failure: { status: number; error?: unknown },
  errors: Errors,
  locale: Locale,
  specific: Partial<Record<number, string>> = {},
): string {
  const detail = (failure.error as { detail?: unknown } | undefined)?.detail;
  if (locale === "en" && typeof detail === "string" && detail) return detail;
  const own = specific[failure.status];
  if (own) return own;
  const generic = (errors as Partial<Record<number, string>>)[failure.status];
  return generic ?? fill(errors.other, { status: failure.status });
}
