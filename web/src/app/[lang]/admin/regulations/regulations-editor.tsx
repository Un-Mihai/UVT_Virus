import Link from "next/link";

import { StatusWord } from "@/components/status-word";
import { sectionTitle } from "@/components/styles";
import { currentLocale, getDictionary } from "@/i18n/dictionary";
import { withLocale } from "@/i18n/locales";
import { api } from "@/lib/api/server";
import { currentUser } from "@/lib/auth/current-user";
import { hasRole } from "@/lib/roles";

import { NewProjectType, TypeActivation } from "./project-types";
import { RegulationFiles } from "./regulation-files";
import { Rules } from "./rules";

type Scope = "client" | "reviewer";
const SCOPES: Scope[] = ["client", "reviewer"];

const tab =
  "rounded-md px-3 py-1.5 text-sm font-medium text-ink-2 transition-colors duration-150 hover:bg-surface-2 hover:text-ink aria-[current=page]:bg-surface-2 aria-[current=page]:text-ink";

async function load(typeParam: string | undefined, scope: Scope) {
  try {
    const [types, checks] = await Promise.all([
      api.GET("/api/project-types"),
      api.GET("/api/checks"),
    ]);
    const all = types.data ?? [];
    const selected =
      all.find((type) => String(type.id) === typeParam) ?? all[0];
    const set = selected
      ? await api.GET(
          "/api/project-types/{project_type_id}/regulations/{scope}",
          {
            params: { path: { project_type_id: selected.id, scope } },
          },
        )
      : null;
    return {
      reachable: true,
      types: all,
      checks: checks.data ?? [],
      selected,
      set: set?.data,
    };
  } catch {
    return {
      reachable: false,
      types: [],
      checks: [],
      selected: undefined,
      set: undefined,
    };
  }
}

/** Pick a project type, then edit one of its two rule sets (DESIGN.md: regulation editor). */
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
  const typeParam = typeof query.type === "string" ? query.type : undefined;
  const { reachable, types, checks, selected, set } = await load(
    typeParam,
    scope,
  );
  if (!reachable) {
    return (
      <p role="alert" className="mt-12 max-w-prose text-bad">
        {dictionary.common.apiUnreachable}
      </p>
    );
  }
  const href = (typeId: number, nextScope: Scope) =>
    withLocale(locale, `/admin/regulations?type=${typeId}&scope=${nextScope}`);

  return (
    <>
      <section aria-labelledby="types-title" className="mt-12">
        <h2 id="types-title" className={sectionTitle}>
          {text.types}
        </h2>
        {types.length === 0 ? (
          <p className="max-w-prose text-ink-2">{text.noTypes}</p>
        ) : (
          <ul className="flex flex-wrap gap-1">
            {types.map((type) => (
              <li key={type.id}>
                <Link
                  href={href(type.id, scope)}
                  aria-current={type.id === selected?.id ? "page" : undefined}
                  className={`${tab} flex items-baseline gap-2 text-base`}
                >
                  {type.name}
                  {!type.active && (
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
      </section>
      {selected && set && (
        <section
          aria-labelledby="type-title"
          className="mt-12 border-t border-line pt-12"
        >
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="grid gap-1">
              <h2
                id="type-title"
                className="text-lg font-semibold tracking-tight"
              >
                {selected.name}
              </h2>
              <p className="flex flex-wrap items-baseline gap-3 text-sm text-ink-2">
                <code>{selected.code}</code>
                <StatusWord state={selected.active ? "ok" : "neutral"}>
                  {selected.active ? text.active : text.inactive}
                </StatusWord>
              </p>
              {selected.description && (
                <p className="max-w-prose text-ink-2">{selected.description}</p>
              )}
            </div>
            <TypeActivation
              projectTypeId={selected.id}
              active={selected.active}
              locale={locale}
              text={text}
              errors={dictionary.errors}
            />
          </div>
          <nav
            aria-label={text.rules}
            className="mt-8 flex flex-wrap gap-1 border-b border-line pb-3"
          >
            {SCOPES.map((option) => (
              <Link
                key={option}
                href={href(selected.id, option)}
                aria-current={option === scope ? "page" : undefined}
                className={tab}
              >
                {dictionary.scopes[option]}
              </Link>
            ))}
          </nav>
          <h3 className="mt-8 mb-4 text-lg font-semibold tracking-tight">
            {dictionary.scopes[scope]}
          </h3>
          <Rules
            key={`${selected.id}-${scope}`}
            rules={set.rules}
            checks={checks}
            projectTypeId={selected.id}
            scope={scope}
            locale={locale}
            text={{ ...text, form: dictionary.form }}
            severity={dictionary.severity}
            errors={dictionary.errors}
          />
          <h3 className="mt-12 mb-4 text-lg font-semibold tracking-tight">
            {text.documents}
          </h3>
          <RegulationFiles
            documents={set.documents}
            projectTypeId={selected.id}
            scope={scope}
            locale={locale}
            text={{ ...text, cancel: dictionary.form.cancel }}
            errors={dictionary.errors}
          />
        </section>
      )}
    </>
  );
}
