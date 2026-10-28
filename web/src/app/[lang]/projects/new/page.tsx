import type { Metadata } from "next";
import { Suspense } from "react";

import { PageHeader } from "@/components/page-header";
import { pageColumn } from "@/components/styles";
import { currentLocale, getDictionary } from "@/i18n/dictionary";
import { api } from "@/lib/api/server";
import { currentUser } from "@/lib/auth/current-user";
import { hasRole } from "@/lib/roles";

import { ApplicationForm } from "../application-form";

export async function generateMetadata(): Promise<Metadata> {
  return { title: (await getDictionary()).application.newTitle };
}

export default async function NewApplicationPage() {
  const dictionary = await getDictionary();
  return (
    <main className={pageColumn}>
      <PageHeader
        title={dictionary.application.newTitle}
        lead={dictionary.application.newLead}
      />
      <Suspense
        fallback={<p className="mt-10 text-ink-3">{dictionary.home.loading}</p>}
      >
        <NewApplication />
      </Suspense>
    </main>
  );
}

async function NewApplication() {
  const [user, dictionary, locale] = await Promise.all([
    currentUser(),
    getDictionary(),
    currentLocale(),
  ]);
  const text = dictionary.application;
  if (!hasRole(user, "client")) {
    return <p className="mt-10 max-w-prose text-ink-2">{text.onlyClients}</p>;
  }
  let types;
  try {
    types = (await api.GET("/api/project-types")).data ?? [];
  } catch {
    return (
      <p role="alert" className="mt-10 max-w-prose text-bad">
        {dictionary.common.apiUnreachable}
      </p>
    );
  }
  const active = types.filter((type) => type.active);
  if (active.length === 0) {
    return <p className="mt-10 max-w-prose text-ink-2">{text.noTypes}</p>;
  }
  return (
    <ApplicationForm
      locale={locale}
      text={{ ...text, form: dictionary.form, errors: dictionary.errors }}
      types={active.map(({ id, name }) => ({ id, name }))}
    />
  );
}
