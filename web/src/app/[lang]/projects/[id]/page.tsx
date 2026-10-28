import type { Metadata } from "next";
import { Suspense } from "react";

import { pageColumn } from "@/components/styles";
import { getDictionary } from "@/i18n/dictionary";

import { Workspace } from "./workspace";

export async function generateMetadata(): Promise<Metadata> {
  return { title: (await getDictionary()).review.title };
}

/** The review workspace; wider than other pages (90rem from 1280px) so the PDF stays legible. */
export default async function ProjectPage({
  params,
}: PageProps<"/[lang]/projects/[id]">) {
  const dictionary = await getDictionary();
  return (
    <main className={`${pageColumn} xl:max-w-360`}>
      <Suspense
        fallback={
          <p aria-busy="true" className="text-ink-3">
            {dictionary.workspace.loading}
          </p>
        }
      >
        <Workspace params={params} />
      </Suspense>
    </main>
  );
}
