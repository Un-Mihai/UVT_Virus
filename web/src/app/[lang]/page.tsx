import { Suspense } from "react";

import { PageHeader } from "@/components/page-header";
import { pageColumn } from "@/components/styles";
import { getDictionary } from "@/i18n/dictionary";

import { HomeSections, HomeSkeleton } from "./home-sections";

export default async function HomePage() {
  const dictionary = await getDictionary();
  return (
    <main className={pageColumn}>
      <PageHeader title={dictionary.app.name} lead={dictionary.home.lead} />
      <Suspense fallback={<HomeSkeleton text={dictionary.home.loading} />}>
        <HomeSections />
      </Suspense>
    </main>
  );
}
