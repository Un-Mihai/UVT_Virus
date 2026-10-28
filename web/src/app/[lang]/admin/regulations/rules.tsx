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
import type { RegulationLevel } from "@/lib/api/upload";

type Rule = components["schemas"]["RuleOut"];
type Text = Dictionary["admin"] & { form: Dictionary["form"] };
type Common = {
  locale: Locale;
  text: Text;
  severity: Dictionary["severity"];
  errors: Dictionary["errors"];
};

/** Requirements an admin writes in plain words, for every project or for a project type;
 *  the model judges documents against them like regulation passages. */
export function WrittenRules({
  rules,
  level,
  ...common
}: Common & { rules: Rule[]; level: RegulationLevel }) {
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
                  level={level}
                  onDone={() => setEditing(null)}
                  {...common}
                />
              ) : (
                <RuleRow
                  rule={rule}
                  onEdit={() => setEditing(rule.id)}
                  {...common}
                />
              )}
            </li>
          ))}
        </ul>
      )}
      <details className="mt-6">
        <summary className="cursor-pointer rounded-control py-2.5 font-semibold text-ink underline decoration-accent decoration-2 underline-offset-4 transition-colors duration-150 hover:text-ink-2">
          {text.newRule}
        </summary>
        <div className="mt-4">
          <RuleForm level={level} {...common} />
        </div>
      </details>
    </>
  );
}

function RuleRow({
  rule,
  onEdit,
  locale,
  text,
  severity,
  errors,
}: Common & { rule: Rule; onEdit: () => void }) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [confirming, setConfirming] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);

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
      <p className="max-w-prose text-ink-2">{rule.description}</p>
      {problem && (
        <p role="alert" className="text-sm text-bad">
          {problem}
        </p>
      )}
    </div>
  );
}

/** Adds a written rule at `level`, or edits `rule` (its code stays: findings cite it). */
function RuleForm({
  rule,
  level,
  onDone,
  locale,
  text,
  severity,
  errors,
}: Common & { rule?: Rule; level: RegulationLevel; onDone?: () => void }) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [problem, setProblem] = useState<string | null>(null);

  function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const value = (name: string) => String(data.get(name) ?? "").trim();
    const fields = {
      title: value("title"),
      description: value("description"),
      severity:
        value("severity") === "warn" ? ("warn" as const) : ("bad" as const),
    };
    startTransition(async () => {
      try {
        const { error, response } = rule
          ? await api.PATCH("/api/rules/{rule_id}", {
              params: { path: { rule_id: rule.id } },
              body: { ...fields, active: data.get("active") === "on" },
            })
          : await api.POST("/api/regulations/rules", {
              body: {
                ...fields,
                code: value("code"),
                scope: level.scope,
                project_type_id: level.project_type_id ?? null,
              },
            });
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

  return (
    <form onSubmit={save} className="grid max-w-2xl gap-4">
      {!rule && (
        <TextField
          name="code"
          label={text.ruleCode}
          hint={text.ruleCodeHint}
          required
          requiredLabel={text.form.required}
        />
      )}
      <TextField
        name="title"
        label={text.ruleTitle}
        required
        requiredLabel={text.form.required}
        defaultValue={rule?.title}
      />
      <TextAreaField
        name="description"
        label={text.ruleText}
        hint={text.ruleTextHint}
        required
        requiredLabel={text.form.required}
        defaultValue={rule?.description}
      />
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
