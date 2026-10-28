"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useState, useTransition } from "react";

import { TextAreaField, TextField } from "@/components/form-field";
import { StatusWord } from "@/components/status-word";
import {
  primaryButton,
  quietButton,
  secondaryButton,
} from "@/components/styles";
import type { Dictionary } from "@/i18n/dictionaries/en";
import type { Locale } from "@/i18n/locales";
import { fill } from "@/i18n/template";
import { api } from "@/lib/api/browser";
import { problemText } from "@/lib/api/problem";
import type { components } from "@/lib/api/schema";

type Item = components["schemas"]["RequiredDocumentOut"];
type Text = Dictionary["admin"] & { form: Dictionary["form"] };
type Common = {
  projectId: number;
  locale: Locale;
  text: Text;
  errors: Dictionary["errors"];
};

/** The documents the applicant of one project must add: read from the regulations by default,
 *  written or edited here (an edited item is kept when the regulations are read again). */
export function RequiredDocumentsEditor({
  items,
  ...common
}: Common & { items: Item[] }) {
  const [editing, setEditing] = useState<number | null>(null);
  const { text } = common;
  return (
    <>
      <ReadRegulations {...common} />
      {items.length === 0 ? (
        <p className="mt-6 max-w-prose text-ink-2">{text.noRequired}</p>
      ) : (
        <ul className="mt-6 divide-y divide-line border-y border-line">
          {items.map((item) => (
            <li key={item.id} className="py-3.5">
              {editing === item.id ? (
                <ItemForm
                  item={item}
                  onDone={() => setEditing(null)}
                  {...common}
                />
              ) : (
                <ItemRow
                  item={item}
                  onEdit={() => setEditing(item.id)}
                  {...common}
                />
              )}
            </li>
          ))}
        </ul>
      )}
      <details className="mt-6">
        <summary className="cursor-pointer rounded-control py-2.5 font-semibold text-ink underline decoration-accent decoration-2 underline-offset-4 transition-colors duration-150 hover:text-ink-2">
          {text.newRequired}
        </summary>
        <div className="mt-4">
          <ItemForm {...common} />
        </div>
      </details>
    </>
  );
}

/** Replaces the items read from the regulations with a fresh reading (takes a while). */
function ReadRegulations({ projectId, locale, text, errors }: Common) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [problem, setProblem] = useState<string | null>(null);

  function read() {
    startTransition(async () => {
      try {
        const { error, response } = await api.POST(
          "/api/projects/{project_id}/required-documents/from-regulations",
          { params: { path: { project_id: projectId } } },
        );
        setProblem(
          error
            ? problemText({ status: response.status, error }, errors, locale)
            : null,
        );
        router.refresh();
      } catch {
        setProblem(errors.network);
      }
    });
  }

  return (
    <div className="mt-6 grid justify-items-start gap-2">
      <button
        type="button"
        disabled={pending}
        onClick={read}
        className={secondaryButton}
      >
        {pending ? text.readingRegulations : text.readRegulations}
      </button>
      {problem && (
        <p role="alert" className="text-sm text-bad">
          {problem}
        </p>
      )}
    </div>
  );
}

function ItemRow({
  item,
  onEdit,
  locale,
  text,
  errors,
}: Common & { item: Item; onEdit: () => void }) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [confirming, setConfirming] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);

  function remove() {
    startTransition(async () => {
      try {
        const { error, response } = await api.DELETE(
          "/api/required-documents/{item_id}",
          { params: { path: { item_id: item.id } } },
        );
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

  const source =
    item.source === "admin"
      ? text.setByAdmin
      : item.regulation_filename && item.regulation_page
        ? fill(text.fromRegulation, {
            file: item.regulation_filename,
            page: item.regulation_page,
          })
        : null;

  return (
    <div className="grid gap-2">
      <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-2">
        <p className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
          <span className="font-medium">{item.name}</span>
          {source && <StatusWord state="neutral">{source}</StatusWord>}
        </p>
        <div className="flex flex-wrap items-center gap-2">
          {confirming ? (
            <>
              <span className="text-sm">
                {fill(text.removeRequiredConfirm, { name: item.name })}
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
      {item.description && (
        <p className="max-w-prose text-ink-2">{item.description}</p>
      )}
      {item.regulation_quote && (
        <p className="max-w-prose text-sm text-ink-3">
          “{item.regulation_quote}”
        </p>
      )}
      {problem && (
        <p role="alert" className="text-sm text-bad">
          {problem}
        </p>
      )}
    </div>
  );
}

/** Adds an item to the list, or edits `item` (which then becomes the administrator's). */
function ItemForm({
  item,
  onDone,
  projectId,
  locale,
  text,
  errors,
}: Common & { item?: Item; onDone?: () => void }) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [problem, setProblem] = useState<string | null>(null);

  function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    const value = (name: string) => String(data.get(name) ?? "").trim();
    const body = { name: value("name"), description: value("description") };
    startTransition(async () => {
      try {
        const { error, response } = item
          ? await api.PATCH("/api/required-documents/{item_id}", {
              params: { path: { item_id: item.id } },
              body,
            })
          : await api.POST("/api/projects/{project_id}/required-documents", {
              params: { path: { project_id: projectId } },
              body,
            });
        if (error) {
          setProblem(
            problemText({ status: response.status, error }, errors, locale),
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
      <TextField
        name="name"
        label={text.requiredName}
        required
        requiredLabel={text.form.required}
        defaultValue={item?.name}
      />
      <TextAreaField
        name="description"
        label={text.requiredDescription}
        hint={text.requiredDescriptionHint}
        defaultValue={item?.description}
      />
      {problem && (
        <p role="alert" className="text-sm text-bad">
          {problem}
        </p>
      )}
      <div className="flex flex-wrap gap-3">
        <button type="submit" disabled={pending} className={primaryButton}>
          {item
            ? pending
              ? text.saving
              : text.save
            : pending
              ? text.adding
              : text.addRequired}
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
