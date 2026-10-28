"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useState, useTransition } from "react";

import { TextAreaField, TextField } from "@/components/form-field";
import { primaryButton, quietButton } from "@/components/styles";
import type { Dictionary } from "@/i18n/dictionaries/en";
import { type Locale, withLocale } from "@/i18n/locales";
import { api } from "@/lib/api/browser";
import { problemText } from "@/lib/api/problem";

type AdminText = Dictionary["admin"];

/** Creates a project type and opens it in the editor. */
export function NewProjectType({
  locale,
  text,
  errors,
}: {
  locale: Locale;
  text: AdminText & { form: Dictionary["form"] };
  errors: Dictionary["errors"];
}) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [problem, setProblem] = useState<string | null>(null);

  function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const value = (name: string) => String(data.get(name) ?? "").trim();
    startTransition(async () => {
      try {
        const {
          data: created,
          error,
          response,
        } = await api.POST("/api/project-types", {
          body: {
            code: value("code"),
            name: value("name"),
            description: value("description"),
          },
        });
        if (created) {
          form.reset();
          setProblem(null);
          router.push(
            withLocale(locale, `/admin/regulations?type=${created.id}`),
          );
          return;
        }
        setProblem(
          problemText({ status: response.status, error }, errors, locale, {
            409: text.duplicateType,
          }),
        );
      } catch {
        setProblem(errors.network);
      }
    });
  }

  return (
    <details className="mt-6">
      <summary className="cursor-pointer rounded-md py-1.5 font-medium text-ink">
        {text.newType}
      </summary>
      <form onSubmit={create} className="mt-4 grid gap-4">
        <TextField
          name="code"
          label={text.code}
          hint={text.codeHint}
          required
          requiredLabel={text.form.required}
        />
        <TextField
          name="name"
          label={text.name}
          required
          requiredLabel={text.form.required}
        />
        <TextAreaField name="description" label={text.description} />
        {problem && (
          <p role="alert" className="text-sm text-bad">
            {problem}
          </p>
        )}
        <div>
          <button type="submit" disabled={pending} className={primaryButton}>
            {pending ? text.creatingType : text.createType}
          </button>
        </div>
      </form>
    </details>
  );
}

/** Inactive types stay in the editor but applicants cannot choose them. */
export function TypeActivation({
  projectTypeId,
  active,
  locale,
  text,
  errors,
}: {
  projectTypeId: number;
  active: boolean;
  locale: Locale;
  text: AdminText;
  errors: Dictionary["errors"];
}) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [problem, setProblem] = useState<string | null>(null);

  function toggle() {
    startTransition(async () => {
      try {
        const { error, response } = await api.PATCH(
          "/api/project-types/{project_type_id}",
          {
            params: { path: { project_type_id: projectTypeId } },
            body: { active: !active },
          },
        );
        setProblem(
          error
            ? problemText({ status: response.status, error }, errors, locale)
            : null,
        );
      } catch {
        setProblem(errors.network);
      }
      router.refresh();
    });
  }

  return (
    <div className="grid justify-items-start gap-1 lg:justify-items-end">
      <button
        type="button"
        disabled={pending}
        onClick={toggle}
        className={quietButton}
      >
        {active ? text.deactivate : text.activate}
      </button>
      {problem && (
        <p role="alert" className="text-sm text-bad">
          {problem}
        </p>
      )}
    </div>
  );
}
