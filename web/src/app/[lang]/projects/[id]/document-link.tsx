"use client";

import { useRouter } from "next/navigation";
import { type ChangeEvent, useState, useTransition } from "react";

import { SelectField } from "@/components/form-field";
import type { Dictionary } from "@/i18n/dictionaries/en";
import type { Locale } from "@/i18n/locales";
import { api } from "@/lib/api/browser";
import { problemText } from "@/lib/api/problem";

/** Picks the item of the list of documents to add that an uploaded document is for. */
export function DocumentLink({
  projectId,
  documentId,
  current,
  items,
  locale,
  text,
  errors,
}: {
  projectId: number;
  documentId: number;
  current: number | null;
  items: { id: number; name: string }[];
  locale: Locale;
  text: Pick<Dictionary["documents"], "linkLabel" | "linkNone">;
  errors: Dictionary["errors"];
}) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [selected, setSelected] = useState(current);
  const [problem, setProblem] = useState<string | null>(null);

  function change(event: ChangeEvent<HTMLSelectElement>) {
    const next =
      event.currentTarget.value === ""
        ? null
        : Number(event.currentTarget.value);
    setSelected(next);
    startTransition(async () => {
      try {
        const { error, response } = await api.PATCH(
          "/api/projects/{project_id}/documents/{document_id}",
          {
            params: {
              path: { project_id: projectId, document_id: documentId },
            },
            body: { required_document_id: next },
          },
        );
        if (error) {
          setSelected(current);
          setProblem(
            problemText({ status: response.status, error }, errors, locale),
          );
          return;
        }
        setProblem(null);
      } catch {
        setSelected(current);
        setProblem(errors.network);
      }
      router.refresh();
    });
  }

  return (
    <div className="grid max-w-sm gap-1">
      <SelectField
        label={text.linkLabel}
        value={selected ?? ""}
        onChange={change}
        disabled={pending}
        error={problem ?? undefined}
      >
        <option value="">{text.linkNone}</option>
        {items.map((item) => (
          <option key={item.id} value={item.id}>
            {item.name}
          </option>
        ))}
      </SelectField>
    </div>
  );
}
