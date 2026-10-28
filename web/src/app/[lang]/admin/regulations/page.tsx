import type { Metadata } from "next";
import { Suspense } from "react";

import { PageHeader } from "@/components/page-header";
import { pageColumn } from "@/components/styles";
import { getDictionary } from "@/i18n/dictionary";

import { RegulationsEditor } from "./regulations-editor";

export async function generateMetadata(): Promise<Metadata> {
  return { title: (await getDictionary()).admin.title };
}

export default async function RegulationsPage({
  searchParams,
}: PageProps<"/[lang]/admin/regulations">) {
  const dictionary = await getDictionary();
  return (
    <main className={pageColumn}>
      <PageHeader title={dictionary.admin.title} lead={dictionary.admin.lead} />
      <Suspense
        fallback={
          <p aria-busy="true" className="mt-12 text-ink-3">
            {dictionary.home.loading}
          </p>
        }
      >
        <RegulationsEditor searchParams={searchParams} />
      </Suspense>
    </main>
  );
}
