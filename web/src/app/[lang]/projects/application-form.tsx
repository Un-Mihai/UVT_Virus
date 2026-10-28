"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type FormEvent, useState, useTransition } from "react";

import { SelectField, TextField } from "@/components/form-field";
import { primaryButton, quietButton } from "@/components/styles";
import type { Dictionary } from "@/i18n/dictionaries/en";
import { type Locale, withLocale } from "@/i18n/locales";
import { fill } from "@/i18n/template";
import { api } from "@/lib/api/browser";
import { problemText } from "@/lib/api/problem";

type Existing = {
  projectId: number;
  typeName: string;
  title: string;
  form: Record<string, unknown>;
};

type Text = Dictionary["application"] & {
  form: Dictionary["form"];
  errors: Dictionary["errors"];
};

const FIELDS = [
  "applicant_name",
  "applicant_cui",
  "legal_representative_name",
  "legal_representative_cnp",
  "requested_amount",
  "iban",
  "start_date",
  "end_date",
] as const;

/** Field names a 422 answer points at ("loc": ["body", "form", "iban"]). */
function invalidFields(error: unknown): Set<string> {
  const detail = (error as { detail?: unknown } | undefined)?.detail;
  if (!Array.isArray(detail)) return new Set();
  return new Set(
    detail.map((item: { loc?: unknown[] }) => String(item.loc?.at(-1) ?? "")),
  );
}

/** The application form: creates a project, or edits one that is still a draft. */
export function ApplicationForm({
  locale,
  text,
  types,
  existing,
}: {
  locale: Locale;
  text: Text;
  types: { id: number; name: string }[];
  existing?: Existing;
}) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [problem, setProblem] = useState<string | null>(null);
  const [invalid, setInvalid] = useState<Set<string>>(new Set());
  const previous = (name: string) => {
    const value = existing?.form[name];
    return typeof value === "string" ? value : "";
  };
  const error = (name: string) =>
    invalid.has(name) ? text.form.invalid : undefined;
  const maskedCnp = previous("legal_representative_cnp_masked");

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const value = (name: string) => String(data.get(name) ?? "").trim();
    const form = Object.fromEntries(
      FIELDS.map((name) => [name, value(name) || null]),
    ) as Record<(typeof FIELDS)[number], string | null>;
    const application = { ...form, applicant_name: value("applicant_name") };
    startTransition(async () => {
      try {
        const result = existing
          ? await api.PATCH("/api/projects/{project_id}", {
              params: { path: { project_id: existing.projectId } },
              body: { title: value("title"), form: application },
            })
          : await api.POST("/api/projects", {
              body: {
                project_type_id: Number(data.get("project_type_id")),
                title: value("title"),
                form: application,
              },
            });
        if (result.data) {
          router.push(withLocale(locale, `/projects/${result.data.id}`));
          return;
        }
        setInvalid(invalidFields(result.error));
        setProblem(
          problemText(
            { status: result.response.status, error: result.error },
            text.errors,
            locale,
          ),
        );
      } catch {
        setProblem(text.errors.network);
      }
    });
  }

  const cancelHref = withLocale(
    locale,
    existing ? `/projects/${existing.projectId}` : "/",
  );
  return (
    <form onSubmit={submit} className="panel mt-10 grid max-w-3xl gap-7">
      {existing ? (
        <p className="text-ink-2">
          {text.projectType}:{" "}
          <span className="font-medium text-ink">{existing.typeName}</span>
        </p>
      ) : (
        <SelectField
          name="project_type_id"
          label={text.projectType}
          required
          requiredLabel={text.form.required}
          defaultValue={types[0]?.id}
        >
          {types.map((type) => (
            <option key={type.id} value={type.id}>
              {type.name}
            </option>
          ))}
        </SelectField>
      )}
      <TextField
        name="title"
        label={text.title}
        hint={text.titleHint}
        required
        requiredLabel={text.form.required}
        defaultValue={existing?.title}
        error={error("title")}
      />
      <TextField
        name="applicant_name"
        label={text.applicantName}
        hint={text.applicantNameHint}
        required
        requiredLabel={text.form.required}
        autoComplete="organization"
        defaultValue={previous("applicant_name")}
        error={error("applicant_name")}
      />
      <div className="grid gap-6 sm:grid-cols-2">
        <TextField
          name="applicant_cui"
          label={text.applicantCui}
          hint={text.applicantCuiHint}
          defaultValue={previous("applicant_cui")}
          error={error("applicant_cui")}
        />
        <TextField
          name="iban"
          label={text.iban}
          hint={text.ibanHint}
          defaultValue={previous("iban")}
          error={error("iban")}
        />
      </div>
      <div className="grid gap-6 sm:grid-cols-2">
        <TextField
          name="legal_representative_name"
          label={text.representativeName}
          autoComplete="name"
          defaultValue={previous("legal_representative_name")}
          error={error("legal_representative_name")}
        />
        <TextField
          name="legal_representative_cnp"
          label={text.representativeCnp}
          hint={
            maskedCnp
              ? fill(text.representativeCnpKeep, { masked: maskedCnp })
              : text.representativeCnpHint
          }
          inputMode="numeric"
          autoComplete="off"
          error={error("legal_representative_cnp")}
        />
      </div>
      <TextField
        name="requested_amount"
        label={text.requestedAmount}
        hint={text.requestedAmountHint}
        inputMode="decimal"
        defaultValue={previous("requested_amount")}
        error={error("requested_amount")}
      />
      <div className="grid gap-6 sm:grid-cols-2">
        <TextField
          name="start_date"
          label={text.startDate}
          hint={text.dateHint}
          defaultValue={previous("start_date")}
          error={error("start_date")}
        />
        <TextField
          name="end_date"
          label={text.endDate}
          hint={text.dateHint}
          defaultValue={previous("end_date")}
          error={error("end_date")}
        />
      </div>
      {problem && (
        <p role="alert" className="max-w-prose text-bad">
          {problem}
        </p>
      )}
      <div className="flex flex-wrap items-center gap-3 border-t border-line pt-6">
        <button type="submit" disabled={pending} className={primaryButton}>
          {existing
            ? pending
              ? text.saving
              : text.save
            : pending
              ? text.creating
              : text.create}
        </button>
        <Link href={cancelHref} className={quietButton}>
          {text.form.cancel}
        </Link>
      </div>
    </form>
  );
}
