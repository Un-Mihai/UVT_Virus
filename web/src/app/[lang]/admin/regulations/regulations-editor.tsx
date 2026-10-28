import Link from "next/link";

import { StatusWord } from "@/components/status-word";
import { sectionTitle } from "@/components/styles";
import type { Dictionary } from "@/i18n/dictionaries/en";
import { currentLocale, getDictionary } from "@/i18n/dictionary";
import { type Locale, withLocale } from "@/i18n/locales";
import { api } from "@/lib/api/server";
import { currentUser } from "@/lib/auth/current-user";
import { hasRole } from "@/lib/roles";

import { NewProjectType, TypeActivation } from "./project-types";
import { RegulationFiles } from "./regulation-files";
import { WrittenRules } from "./rules";

type Scope = "client" | "reviewer";
const SCOPES: Scope[] = ["client", "reviewer"];

/** Where regulations apply: every project, every project of a type, or one project. */
type Level =
  | { kind: "every" }
  | { kind: "type"; id: number }
  | { kind: "project"; id: number };

const tab =
  "inline-flex min-h-11 items-center rounded-control px-4 py-2.5 text-sm font-semibold text-ink-2 transition-colors duration-150 hover:bg-surface-2 hover:text-ink aria-[current=page]:bg-accent aria-[current=page]:text-on-accent";

function levelOf(query: Record<string, string | string[] | undefined>): Level {
  const id = (value: unknown) =>
    typeof value === "string" && /^\d+$/.test(value) ? Number(value) : null;
  const type = id(query.type);
  if (type !== null) return { kind: "type", id: type };
  const project = id(query.project);
  if (project !== null) return { kind: "project", id: project };
  return { kind: "every" };
}

function levelParams(level: Level) {
  if (level.kind === "type") return { project_type_id: level.id };
  if (level.kind === "project") return { project_id: level.id };
  return {};
}

function href(locale: Locale, level: Level, scope: Scope) {
  const where =
    level.kind === "type"
      ? `type=${level.id}&`
      : level.kind === "project"
        ? `project=${level.id}&`
        : "";
  return withLocale(locale, `/admin/regulations?${where}scope=${scope}`);
}

async function load(level: Level, scope: Scope) {
  try {
    const [types, projects, set] = await Promise.all([
      api.GET("/api/project-types"),
      api.GET("/api/admin/projects"),
      api.GET("/api/regulations", {
        params: { query: { scope, ...levelParams(level) } },
      }),
    ]);
    return {
      reachable: true,
      types: types.data ?? [],
      projects: projects.data ?? [],
      set: set.data,
    };
  } catch {
    return { reachable: false, types: [], projects: [], set: undefined };
  }
}

/** Pick where regulations apply, then edit the client or the reviewer set there
 *  (DESIGN.md: regulation editor). */
export async function RegulationsEditor({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const [query, dictionary, locale, user] = await Promise.all([
    searchParams,
    getDictionary(),
    currentLocale(),
    currentUser(),
  ]);
  const text = dictionary.admin;
  if (!hasRole(user, "admin")) {
    return <p className="mt-12 max-w-prose text-ink-2">{text.onlyAdmins}</p>;
  }
  const scope: Scope = query.scope === "reviewer" ? "reviewer" : "client";
  const level = levelOf(query);
  const { reachable, types, projects, set } = await load(level, scope);
  if (!reachable) {
    return (
      <p role="alert" className="mt-12 max-w-prose text-bad">
        {dictionary.common.apiUnreachable}
      </p>
    );
  }
  const type =
    level.kind === "type" ? types.find((t) => t.id === level.id) : undefined;
  const project =
    level.kind === "project"
      ? projects.find((p) => p.id === level.id)
      : undefined;
  const typeName = (id: number) => types.find((t) => t.id === id)?.name ?? "";
  const current = (candidate: Level) =>
    candidate.kind === level.kind &&
    (candidate.kind === "every" ||
      (level.kind !== "every" && candidate.id === level.id))
      ? "page"
      : undefined;

  return (
    <>
      <nav aria-labelledby="levels-title" className="panel mt-10 grid gap-6">
        <h2 id="levels-title" className="text-xl font-bold tracking-tight">
          {text.appliesTo}
        </h2>
        <ul className="flex flex-wrap gap-1">
          <li>
            <Link
              href={href(locale, { kind: "every" }, scope)}
              aria-current={current({ kind: "every" })}
              className={`${tab} text-base`}
            >
              {text.everyProject}
            </Link>
          </li>
        </ul>
        <div className="grid gap-2">
          <h3 className="text-sm font-medium text-ink-3">{text.types}</h3>
          {types.length === 0 ? (
            <p className="max-w-prose text-ink-2">{text.noTypes}</p>
          ) : (
            <ul className="flex flex-wrap gap-1">
              {types.map((candidate) => (
                <li key={candidate.id}>
                  <Link
                    href={href(
                      locale,
                      { kind: "type", id: candidate.id },
                      scope,
                    )}
                    aria-current={current({ kind: "type", id: candidate.id })}
                    className={`${tab} flex items-baseline gap-2 text-base`}
                  >
                    {candidate.name}
                    {!candidate.active && (
                      <span className="text-sm font-normal text-ink-3">
                        {text.inactive}
                      </span>
                    )}
                  </Link>
                </li>
              ))}
            </ul>
          )}
          <NewProjectType
            locale={locale}
            text={{ ...text, form: dictionary.form }}
            errors={dictionary.errors}
          />
        </div>
        <div className="grid gap-2">
          <h3 className="text-sm font-medium text-ink-3">{text.projects}</h3>
          {projects.length === 0 ? (
            <p className="max-w-prose text-ink-2">{text.noProjects}</p>
          ) : (
            <ul className="flex flex-wrap gap-1">
              {projects.map((candidate) => (
                <li key={candidate.id}>
                  <Link
                    href={href(
                      locale,
                      { kind: "project", id: candidate.id },
                      scope,
                    )}
                    aria-current={current({
                      kind: "project",
                      id: candidate.id,
                    })}
                    className={`${tab} flex items-baseline gap-2 text-base`}
                  >
                    {candidate.title}
                    <span className="text-sm font-normal text-ink-3">
                      {typeName(candidate.project_type_id)}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      </nav>
      {set && (
        <section aria-labelledby="level-title" className="panel mt-8">
          <LevelHeading
            level={level}
            name={type?.name ?? project?.title ?? text.everyProject}
            typeActive={type?.active}
            locale={locale}
            dictionary={dictionary}
          />
          <nav
            aria-label={text.scopes}
            className="mt-8 flex flex-wrap gap-2 border-b border-line pb-4"
          >
            {SCOPES.map((option) => (
              <Link
                key={option}
                href={href(locale, level, option)}
                aria-current={option === scope ? "page" : undefined}
                className={tab}
              >
                {dictionary.scopes[option]}
              </Link>
            ))}
          </nav>
          <h3 className="mt-8 text-lg font-semibold tracking-tight">
            {dictionary.scopes[scope]}
          </h3>
          <h4 className="mt-6 mb-3 font-semibold">{text.documents}</h4>
          <RegulationFiles
            key={`documents-${level.kind}-${"id" in level ? level.id : 0}-${scope}`}
            documents={set.documents}
            level={{ scope, ...levelParams(level) }}
            locale={locale}
            text={{ ...text, cancel: dictionary.form.cancel }}
            errors={dictionary.errors}
          />
          <h4 className="mt-10 mb-3 font-semibold">{text.rules}</h4>
          {level.kind === "project" ? (
            <p className="max-w-prose text-ink-2">{text.projectRules}</p>
          ) : (
            <WrittenRules
              key={`rules-${level.kind}-${"id" in level ? level.id : 0}-${scope}`}
              rules={set.rules}
              level={{ scope, ...levelParams(level) }}
              locale={locale}
              text={{ ...text, form: dictionary.form }}
              severity={dictionary.severity}
              errors={dictionary.errors}
            />
          )}
        </section>
      )}
    </>
  );
}

function LevelHeading({
  level,
  name,
  typeActive,
  locale,
  dictionary,
}: {
  level: Level;
  name: string;
  typeActive: boolean | undefined;
  locale: Locale;
  dictionary: Dictionary;
}) {
  const text = dictionary.admin;
  const lead =
    level.kind === "type"
      ? text.levelType
      : level.kind === "project"
        ? text.levelProject
        : text.levelEvery;
  return (
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div className="grid gap-1">
        <h2 id="level-title" className={`${sectionTitle} mb-0`}>
          {name}
        </h2>
        {level.kind === "type" && typeActive !== undefined && (
          <StatusWord state={typeActive ? "ok" : "neutral"}>
            {typeActive ? text.active : text.inactive}
          </StatusWord>
        )}
        <p className="max-w-prose text-ink-2">{lead}</p>
      </div>
      {level.kind === "type" && typeActive !== undefined && (
        <TypeActivation
          projectTypeId={level.id}
          active={typeActive}
          locale={locale}
          text={text}
          errors={dictionary.errors}
        />
      )}
    </div>
  );
}
