"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { quietButton } from "@/components/styles";
import type { Dictionary } from "@/i18n/dictionaries/en";
import type { Locale } from "@/i18n/locales";
import { fill } from "@/i18n/template";
import { api } from "@/lib/api/browser";
import { problemText } from "@/lib/api/problem";

/** Read a document's scanned pages again, or delete it (with a confirmation step). */
export function DocumentActions({
  projectId,
  documentId,
  filename,
  canReadAgain,
  canDelete,
  locale,
  text,
  errors,
}: {
  projectId: number;
  documentId: number;
  filename: string;
  canReadAgain: boolean;
  canDelete: boolean;
  locale: Locale;
  text: Dictionary["documents"] & { cancel: string };
  errors: Dictionary["errors"];
}) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [action, setAction] = useState<"read" | "delete" | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const path = {
    params: { path: { project_id: projectId, document_id: documentId } },
  };
  if (!canReadAgain && !canDelete) return null;

  function act(
    kind: "read" | "delete",
    call: () => Promise<{ error?: unknown; response: Response }>,
  ) {
    setAction(kind);
    startTransition(async () => {
      try {
        const { error, response } = await call();
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
    <div className="flex flex-wrap items-center gap-2">
      {canReadAgain && (
        <button
          type="button"
          disabled={pending}
          onClick={() =>
            act("read", () =>
              api.POST(
                "/api/projects/{project_id}/documents/{document_id}/read-scans",
                path,
              ),
            )
          }
          className={quietButton}
        >
          {pending && action === "read" ? text.readingAgain : text.readAgain}
        </button>
      )}
      {canDelete && !confirming && (
        <button
          type="button"
          disabled={pending}
          onClick={() => setConfirming(true)}
          className={quietButton}
        >
          {text.remove}
        </button>
      )}
      {confirming && (
        <span className="flex flex-wrap items-center gap-2 text-sm">
          <span>{fill(text.removeConfirm, { name: filename })}</span>
          <button
            type="button"
            disabled={pending}
            onClick={() =>
              act("delete", () =>
                api.DELETE(
                  "/api/projects/{project_id}/documents/{document_id}",
                  path,
                ),
              )
            }
            className={`${quietButton} text-bad hover:text-bad`}
          >
            {pending && action === "delete" ? text.removing : text.remove}
          </button>
          <button
            type="button"
            disabled={pending}
            onClick={() => setConfirming(false)}
            className={quietButton}
          >
            {text.cancel}
          </button>
        </span>
      )}
      {problem && (
        <p role="alert" className="w-full text-sm text-bad">
          {problem}
        </p>
      )}
    </div>
  );
}
