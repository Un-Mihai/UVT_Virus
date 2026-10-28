import Link from "next/link";

import { StatusWord } from "@/components/status-word";
import { primaryButton, sectionTitle, textLink } from "@/components/styles";
import type { Dictionary } from "@/i18n/dictionaries/en";
import { currentLocale, getDictionary } from "@/i18n/dictionary";
import { type Locale, withLocale } from "@/i18n/locales";
import type { components } from "@/lib/api/schema";
import { api } from "@/lib/api/server";
import { currentUser } from "@/lib/auth/current-user";
import { formatDateTime } from "@/lib/format";
import { hasRole } from "@/lib/roles";

type ProjectSummary = components["schemas"]["ProjectSummary"];
type ProjectType = components["schemas"]["ProjectTypeOut"];

async function load(withProjects: boolean) {
  try {
    const [projects, types] = await Promise.all([
      withProjects ? api.GET("/api/projects") : null,
      api.GET("/api/project-types"),
    ]);
    return {
      reachable: true,
      projects: projects?.data ?? [],
      types: types.data ?? [],
    };
  } catch {
    return { reachable: false, projects: [], types: [] };
  }
}

/** One section per role the signed-in user holds; the API decides what each may see. */
export async function HomeSections() {
  const [user, dictionary, locale] = await Promise.all([
    currentUser(),
    getDictionary(),
    currentLocale(),
  ]);
  const isClient = hasRole(user, "client");
  const isReviewer = hasRole(user, "reviewer");
  const isAdmin = hasRole(user, "admin");
  if (!isClient && !isReviewer && !isAdmin) {
    return (
      <p className="mt-12 max-w-prose text-ink-2">{dictionary.home.noRole}</p>
    );
  }

  const { reachable, projects, types } = await load(isClient || isReviewer);
  if (!reachable) {
    return (
      <p role="alert" className="mt-12 max-w-prose text-bad">
        {dictionary.common.apiUnreachable}
      </p>
    );
  }
  const typeNames = new Map(types.map((type) => [type.id, type.name]));
  const view = { dictionary, locale, typeNames };

  return (
    <>
      {isReviewer ? (
        <SubmittedProjects projects={projects} {...view} />
      ) : (
        isClient && <ClientApplications projects={projects} {...view} />
      )}
      {isAdmin && (
        <ProjectTypes types={types} dictionary={dictionary} locale={locale} />
      )}
    </>
  );
}

type View = {
  dictionary: Dictionary;
  locale: Locale;
  typeNames: Map<number, string>;
};

function ClientApplications({
  projects,
  dictionary,
  locale,
  typeNames,
}: View & { projects: ProjectSummary[] }) {
  const text = dictionary.home.client;
  return (
    <section className="mt-12" aria-labelledby="applications-title">
      <div className="mb-4 flex flex-wrap items-baseline justify-between gap-3">
        <h2
          id="applications-title"
          className="text-lg font-semibold tracking-tight"
        >
          {text.title}
        </h2>
        <Link
          href={withLocale(locale, "/projects/new")}
          className={primaryButton}
        >
          {text.newApplication}
        </Link>
      </div>
      {projects.length === 0 ? (
        <p className="max-w-prose text-ink-2">{text.empty}</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[40rem] text-left text-sm">
            <thead className="border-b border-line-strong text-ink-3">
              <tr>
                <th className="py-2 pr-4 font-medium">{text.title_column}</th>
                <th className="py-2 pr-4 font-medium">{text.type_column}</th>
                <th className="py-2 pr-4 font-medium">{text.status_column}</th>
                <th className="py-2 font-medium">{text.created_column}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line tabular-nums">
              {projects.map((project) => (
                <tr key={project.id}>
                  <td className="py-2.5 pr-4">
                    <Link
                      href={withLocale(locale, `/projects/${project.id}`)}
                      className={textLink}
                    >
                      {project.title}
                    </Link>
                  </td>
                  <td className="py-2.5 pr-4 text-ink-2">
                    {typeNames.get(project.project_type_id)}
                  </td>
                  <td className="py-2.5 pr-4">
                    <StatusWord
                      state={project.status === "submitted" ? "ok" : "neutral"}
                    >
                      {dictionary.projectStatus[project.status]}
                    </StatusWord>
                  </td>
                  <td className="py-2.5 whitespace-nowrap text-ink-2">
                    {formatDateTime(project.created_at, locale)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function SubmittedProjects({
  projects,
  dictionary,
  locale,
  typeNames,
}: View & { projects: ProjectSummary[] }) {
  const text = dictionary.home.reviewer;
  return (
    <section className="mt-12" aria-labelledby="submitted-title">
      <h2 id="submitted-title" className={sectionTitle}>
        {text.title}
      </h2>
      {projects.length === 0 ? (
        <p className="max-w-prose text-ink-2">{text.empty}</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[36rem] text-left text-sm">
            <thead className="border-b border-line-strong text-ink-3">
              <tr>
                <th className="py-2 pr-4 font-medium">{text.title_column}</th>
                <th className="py-2 pr-4 font-medium">{text.type_column}</th>
                <th className="py-2 font-medium">{text.submitted_column}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line tabular-nums">
              {projects.map((project) => (
                <tr key={project.id}>
                  <td className="py-2.5 pr-4">
                    <Link
                      href={withLocale(locale, `/projects/${project.id}`)}
                      className={textLink}
                    >
                      {project.title}
                    </Link>
                  </td>
                  <td className="py-2.5 pr-4 text-ink-2">
                    {typeNames.get(project.project_type_id)}
                  </td>
                  <td className="py-2.5 whitespace-nowrap text-ink-2">
                    {project.submitted_at &&
                      formatDateTime(project.submitted_at, locale)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function ProjectTypes({
  types,
  dictionary,
  locale,
}: {
  types: ProjectType[];
  dictionary: Dictionary;
  locale: Locale;
}) {
  const text = dictionary.home.admin;
  return (
    <section className="mt-12" aria-labelledby="types-title">
      <div className="mb-4 flex flex-wrap items-baseline justify-between gap-3">
        <h2 id="types-title" className="text-lg font-semibold tracking-tight">
          {text.title}
        </h2>
        <Link
          href={withLocale(locale, "/admin/regulations")}
          className={primaryButton}
        >
          {text.editRegulations}
        </Link>
      </div>
      <p className="mb-4 max-w-prose text-ink-2">{text.lead}</p>
      {types.length === 0 ? (
        <p className="max-w-prose text-ink-2">{text.empty}</p>
      ) : (
        <ul className="divide-y divide-line border-y border-line">
          {types.map((type) => (
            <li
              key={type.id}
              className="flex flex-wrap items-baseline gap-x-4 gap-y-1 py-3.5"
            >
              <Link
                href={withLocale(locale, `/admin/regulations?type=${type.id}`)}
                className={textLink}
              >
                {type.name}
              </Link>
              <code className="text-sm text-ink-3">{type.code}</code>
              {!type.active && (
                <StatusWord state="neutral">{text.inactive}</StatusWord>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

/** Says what is loading while the sections wait for the API. */
export function HomeSkeleton({ text }: { text: string }) {
  return (
    <section className="mt-12" aria-busy="true">
      <p className="text-ink-3">{text}</p>
    </section>
  );
}
