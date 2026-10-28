import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Suspense } from "react";

import { PageHeader } from "@/components/page-header";
import { pageColumn } from "@/components/styles";
import { currentLocale, getDictionary } from "@/i18n/dictionary";
import { api } from "@/lib/api/server";
import { currentUser } from "@/lib/auth/current-user";
import { hasRole } from "@/lib/roles";

import { ApplicationForm } from "../../application-form";

export async function generateMetadata(): Promise<Metadata> {
  return { title: (await getDictionary()).application.editTitle };
}

export default async function EditApplicationPage({
  params,
}: PageProps<"/[lang]/projects/[id]/edit">) {
  const dictionary = await getDictionary();
  return (
    <main className={pageColumn}>
      <PageHeader
        title={dictionary.application.editTitle}
        lead={dictionary.application.editLead}
      />
      <Suspense
        fallback={
          <p className="mt-10 text-ink-3">{dictionary.workspace.loading}</p>
        }
      >
        <EditApplication params={params} />
      </Suspense>
    </main>
  );
}

async function EditApplication({
  params,
}: Pick<PageProps<"/[lang]/projects/[id]/edit">, "params">) {
  const projectId = Number((await params).id);
  if (!Number.isInteger(projectId)) notFound();
  const [user, dictionary, locale] = await Promise.all([
    currentUser(),
    getDictionary(),
    currentLocale(),
  ]);
  const text = dictionary.application;
  if (!hasRole(user, "client")) {
    return <p className="mt-10 max-w-prose text-ink-2">{text.onlyClients}</p>;
  }
  let project, types;
  try {
    const [projectAnswer, typesAnswer] = await Promise.all([
      api.GET("/api/projects/{project_id}", {
        params: { path: { project_id: projectId } },
      }),
      api.GET("/api/project-types"),
    ]);
    project = projectAnswer.data;
    types = typesAnswer.data ?? [];
  } catch {
    return (
      <p role="alert" className="mt-10 max-w-prose text-bad">
        {dictionary.common.apiUnreachable}
      </p>
    );
  }
  if (!project) notFound();
  if (project.status !== "draft" || project.owner_id !== user?.id) {
    return <p className="mt-10 max-w-prose text-ink-2">{text.notEditable}</p>;
  }
  return (
    <ApplicationForm
      locale={locale}
      text={{ ...text, form: dictionary.form, errors: dictionary.errors }}
      types={[]}
      existing={{
        projectId: project.id,
        typeName:
          types.find((type) => type.id === project.project_type_id)?.name ?? "",
        title: project.title,
        form: project.form,
      }}
    />
  );
}
