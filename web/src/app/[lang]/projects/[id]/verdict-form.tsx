"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { TextAreaField } from "@/components/form-field";
import { primaryButton, secondaryButton } from "@/components/styles";
import type { Dictionary } from "@/i18n/dictionaries/en";
import { type Locale, withLocale } from "@/i18n/locales";
import { api } from "@/lib/api/browser";
import { problemText } from "@/lib/api/problem";

type Verdict = "approved" | "changes_requested";

/** People decide: the reviewer approves a file or sends it back with a note for the applicant. */
export function VerdictForm({
  projectId,
  locale,
  initialNote,
  text,
  errors,
}: {
  projectId: number;
  locale: Locale;
  initialNote: string;
  text: Dictionary["verdict"];
  errors: Dictionary["errors"];
}) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [action, setAction] = useState<Verdict | null>(null);
  const [note, setNote] = useState(initialNote);
  const [problem, setProblem] = useState<string | null>(null);

  function record(verdict: Verdict) {
    setAction(verdict);
    startTransition(async () => {
      try {
        const { error, response } = await api.PUT(
          "/api/projects/{project_id}/verdict",
          {
            params: { path: { project_id: projectId } },
            body: { verdict, note },
          },
        );
        if (error) {
          setProblem(
            problemText({ status: response.status, error }, errors, locale, {
              422: text.noteRequired,
            }),
          );
          return;
        }
        setProblem(null);
        // A file sent back leaves the reviewer's list, so the page would only say "not found".
        if (verdict === "changes_requested") {
          router.push(withLocale(locale, "/"));
        } else {
          router.refresh();
        }
      } catch {
        setProblem(errors.network);
      }
    });
  }

  return (
    <div className="grid max-w-prose gap-4">
      <TextAreaField
        label={text.noteLabel}
        hint={text.noteHint}
        value={note}
        onChange={(event) => setNote(event.target.value)}
        maxLength={2000}
      />
      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={() => record("approved")}
          disabled={pending}
          className={primaryButton}
        >
          {pending && action === "approved" ? text.saving : text.approve}
        </button>
        <button
          type="button"
          onClick={() => record("changes_requested")}
          disabled={pending || note.trim() === ""}
          className={secondaryButton}
        >
          {pending && action === "changes_requested"
            ? text.saving
            : text.requestChanges}
        </button>
      </div>
      {problem && (
        <p role="alert" className="text-sm text-bad">
          {problem}
        </p>
      )}
    </div>
  );
}
