import Link from "next/link";

import { PageHeader } from "@/components/page-header";
import { pageColumn, textLink } from "@/components/styles";
import { currentLocale, getDictionary } from "@/i18n/dictionary";
import { withLocale } from "@/i18n/locales";

export default async function NotFound() {
  const [dictionary, locale] = await Promise.all([
    getDictionary(),
    currentLocale(),
  ]);
  return (
    <main className={pageColumn}>
      <PageHeader
        title={dictionary.notFound.title}
        lead={dictionary.notFound.body}
      />
      <p className="mt-8">
        <Link href={withLocale(locale, "/")} className={textLink}>
          {dictionary.notFound.home}
        </Link>
      </p>
    </main>
  );
}
