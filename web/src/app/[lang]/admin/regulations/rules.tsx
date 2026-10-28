"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useState, useTransition } from "react";

import { SelectField, TextAreaField, TextField } from "@/components/form-field";
import { StatusWord } from "@/components/status-word";
import { primaryButton, quietButton } from "@/components/styles";
import type { Dictionary } from "@/i18n/dictionaries/en";
import type { Locale } from "@/i18n/locales";
import { fill } from "@/i18n/template";
import { api } from "@/lib/api/browser";
import { problemText } from "@/lib/api/problem";
import type { components } from "@/lib/api/schema";

type Rule = components["schemas"]["RuleOut"];
type Check = components["schemas"]["CheckOut"];
type Scope = "client" | "reviewer";
type Text = Dictionary["admin"] & { form: Dictionary["form"] };
type Common = {
  locale: Locale;
  text: Text;
  severity: Dictionary["severity"];
  errors: Dictionary["errors"];
};

/** The params a check takes, as its JSON Schema says (string, number, boolean, list). */
type ParamSchema = {
  properties?: Record<
    string,
    {
      type?: string;
      title?: string;
      default?: unknown;
      items?: { type?: string };
    }
  >;
  required?: string[];
};

/** One rule set's rules: read, edit in place, delete, add. */
export function Rules({
  rules,
  checks,
  projectTypeId,
  scope,
  ...common
}: Common & {
  rules: Rule[];
  checks: Check[];
  projectTypeId: number;
  scope: Scope;
}) {
  const [editing, setEditing] = useState<number | null>(null);
  const { text } = common;
  return (
    <>
      {rules.length === 0 ? (
        <p className="max-w-prose text-ink-2">{text.noRules}</p>
      ) : (
        <ul className="divide-y divide-line border-y border-line">
          {rules.map((rule) => (
            <li key={rule.id} className="py-3.5">
              {editing === rule.id ? (
                <RuleForm
                  rule={rule}
                  checks={checks}
                  projectTypeId={projectTypeId}
                  scope={scope}
                  onDone={() => setEditing(null)}
                  {...common}
                />
              ) : (
                <RuleRow
                  rule={rule}
                  check={checks.find((check) => check.id === rule.check_id)}
                  onEdit={() => setEditing(rule.id)}
                  {...common}
                />
              )}
            </li>
          ))}
        </ul>
      )}
      <details className="mt-6">
        <summary className="cursor-pointer rounded-md py-1.5 font-medium text-ink">
          {text.newRule}
        </summary>
        <div className="mt-4">
          <RuleForm
            checks={checks}
            projectTypeId={projectTypeId}
            scope={scope}
            {...common}
          />
        </div>
      </details>
    </>
  );
}

function RuleRow({
  rule,
  check,
  onEdit,
  locale,
  text,
  severity,
  errors,
}: Common & { rule: Rule; check: Check | undefined; onEdit: () => void }) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [confirming, setConfirming] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const explanation =
    rule.kind === "ai"
      ? rule.description
      : (check?.description[locale] ?? check?.description.en ?? rule.check_id);
  const settings = Object.entries(rule.params)
    .map(
      ([name, value]) =>
        `${paramLabel(name, undefined, text)}: ${Array.isArray(value) ? value.join(", ") : String(value)}`,
    )
    .join(" · ");

  function remove() {
    startTransition(async () => {
      try {
        const { error, response } = await api.DELETE("/api/rules/{rule_id}", {
          params: { path: { rule_id: rule.id } },
        });
        setProblem(
          error
            ? problemText({ status: response.status, error }, errors, locale)
            : null,
        );
      } catch {
        setProblem(errors.network);
      }
      setConfirming(false);
      router.refresh();
    });
  }

  return (
    <div className="grid gap-2">
      <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-2">
        <p className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
          <code className="text-sm text-ink-2">{rule.code}</code>
          <span className="font-medium">{rule.title}</span>
          <span className="text-sm text-ink-2">{text.kinds[rule.kind]}</span>
          <StatusWord state={rule.severity}>
            {severity[rule.severity]}
          </StatusWord>
          {!rule.active && (
            <StatusWord state="neutral">{text.inactive}</StatusWord>
          )}
        </p>
        <div className="flex flex-wrap items-center gap-2">
          {confirming ? (
            <>
              <span className="text-sm">
                {fill(text.removeRuleConfirm, { code: rule.code })}
              </span>
              <button
                type="button"
                disabled={pending}
                onClick={remove}
                className={`${quietButton} text-bad hover:text-bad`}
              >
                {pending ? text.removing : text.remove}
              </button>
              <button
                type="button"
                disabled={pending}
                onClick={() => setConfirming(false)}
                className={quietButton}
              >
                {text.form.cancel}
              </button>
            </>
          ) : (
            <>
              <button type="button" onClick={onEdit} className={quietButton}>
                {text.edit}
              </button>
              <button
                type="button"
                onClick={() => setConfirming(true)}
                className={quietButton}
              >
                {text.remove}
              </button>
            </>
          )}
        </div>
      </div>
      {explanation && (
        <p className="max-w-prose text-pretty text-ink-2">{explanation}</p>
      )}
      {settings && <p className="text-sm text-ink-3">{settings}</p>}
      {problem && (
        <p role="alert" className="text-sm text-bad">
          {problem}
        </p>
      )}
    </div>
  );
}

function paramLabel(name: string, title: string | undefined, text: Text) {
  const labels: Record<string, string> = text.paramLabels;
  return labels[name] ?? title ?? name;
}

/** Adds a rule, or edits `rule` (its code and kind stay; the API keys checks by them). */
function RuleForm({
  rule,
  checks,
  projectTypeId,
  scope,
  onDone,
  locale,
  text,
  severity,
  errors,
}: Common & {
  rule?: Rule;
  checks: Check[];
  projectTypeId: number;
  scope: Scope;
  onDone?: () => void;
}) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [problem, setProblem] = useState<string | null>(null);
  const [kind, setKind] = useState<"check" | "ai">(rule?.kind ?? "check");
  const [checkId, setCheckId] = useState(rule?.check_id ?? checks[0]?.id ?? "");
  const check = checks.find((candidate) => candidate.id === checkId);
  const schema = (check?.params_schema ?? {}) as ParamSchema;
  const properties = Object.entries(schema.properties ?? {});

  function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const value = (name: string) => String(data.get(name) ?? "").trim();
    const params: Record<string, unknown> = {};
    if (kind === "check") {
      for (const [name, property] of properties) {
        const raw = value(`param-${name}`);
        if (property.type === "array") {
          params[name] = raw
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean);
        } else if (property.type === "boolean") {
          params[name] = data.get(`param-${name}`) === "on";
        } else if (property.type === "number" || property.type === "integer") {
          if (raw) params[name] = Number(raw);
        } else if (raw) {
          params[name] = raw;
        }
      }
    }
    const common = {
      title: value("title"),
      description: kind === "ai" ? value("description") : "",
      check_id: kind === "check" ? checkId : null,
      params,
      severity:
        value("severity") === "warn" ? ("warn" as const) : ("bad" as const),
    };
    startTransition(async () => {
      try {
        const { error, response } = rule
          ? await api.PATCH("/api/rules/{rule_id}", {
              params: { path: { rule_id: rule.id } },
              body: { ...common, active: data.get("active") === "on" },
            })
          : await api.POST(
              "/api/project-types/{project_type_id}/regulations/{scope}/rules",
              {
                params: { path: { project_type_id: projectTypeId, scope } },
                body: { ...common, code: value("code"), kind, active: true },
              },
            );
        if (error) {
          setProblem(
            problemText({ status: response.status, error }, errors, locale, {
              409: text.duplicateRule,
            }),
          );
          return;
        }
        setProblem(null);
        form.reset();
        onDone?.();
        router.refresh();
      } catch {
        setProblem(errors.network);
      }
    });
  }

  const current = (name: string, fallback: unknown) => {
    const stored = rule?.params[name] ?? fallback;
    return Array.isArray(stored)
      ? stored.join(", ")
      : stored == null
        ? ""
        : String(stored);
  };

  return (
    <form onSubmit={save} className="grid max-w-2xl gap-4">
      {!rule && (
        <div className="grid gap-4 sm:grid-cols-2">
          <TextField
            name="code"
            label={text.ruleCode}
            hint={text.ruleCodeHint}
            required
            requiredLabel={text.form.required}
          />
          <fieldset className="grid gap-1.5">
            <legend className="mb-1.5 text-sm font-medium text-ink">
              {text.kind}
            </legend>
            {(["check", "ai"] as const).map((option) => (
              <label key={option} className="flex items-center gap-2">
                <input
                  type="radio"
                  name="kind"
                  value={option}
                  checked={kind === option}
                  onChange={() => setKind(option)}
                  className="accent-accent"
                />
                {text.kinds[option]}
              </label>
            ))}
          </fieldset>
        </div>
      )}
      <TextField
        name="title"
        label={text.ruleTitle}
        required
        requiredLabel={text.form.required}
        defaultValue={rule?.title}
      />
      {kind === "check" ? (
        <>
          <SelectField
            name="check_id"
            label={text.check}
            value={checkId}
            onChange={(event) => setCheckId(event.target.value)}
            hint={check?.description[locale] ?? check?.description.en}
          >
            {checks.map((option) => (
              <option key={option.id} value={option.id}>
                {option.id}
              </option>
            ))}
          </SelectField>
          {properties.length > 0 && (
            <fieldset className="grid gap-4">
              <legend className="mb-1 text-sm font-medium text-ink">
                {text.params}
              </legend>
              {properties.map(([name, property]) =>
                property.type === "boolean" ? (
                  <label key={name} className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      name={`param-${name}`}
                      defaultChecked={Boolean(
                        rule?.params[name] ?? property.default,
                      )}
                      className="accent-accent"
                    />
                    {paramLabel(name, property.title, text)}
                  </label>
                ) : (
                  <TextField
                    key={name}
                    name={`param-${name}`}
                    label={paramLabel(name, property.title, text)}
                    hint={property.type === "array" ? text.listHint : undefined}
                    required={schema.required?.includes(name)}
                    requiredLabel={text.form.required}
                    defaultValue={current(name, property.default)}
                  />
                ),
              )}
            </fieldset>
          )}
        </>
      ) : (
        <TextAreaField
          name="description"
          label={text.clause}
          hint={text.clauseHint}
          required
          requiredLabel={text.form.required}
          defaultValue={rule?.description}
        />
      )}
      <SelectField
        name="severity"
        label={text.severity}
        defaultValue={rule?.severity ?? "bad"}
      >
        <option value="bad">{severity.bad}</option>
        <option value="warn">{severity.warn}</option>
      </SelectField>
      {rule && (
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            name="active"
            defaultChecked={rule.active}
            className="accent-accent"
          />
          {text.activeRule}
        </label>
      )}
      {problem && (
        <p role="alert" className="text-sm text-bad">
          {problem}
        </p>
      )}
      <div className="flex flex-wrap gap-3">
        <button type="submit" disabled={pending} className={primaryButton}>
          {rule
            ? pending
              ? text.saving
              : text.save
            : pending
              ? text.addingRule
              : text.addRule}
        </button>
        {onDone && (
          <button type="button" onClick={onDone} className={quietButton}>
            {text.form.cancel}
          </button>
        )}
      </div>
    </form>
  );
}
