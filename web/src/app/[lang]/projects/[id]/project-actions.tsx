"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import {
  primaryButton,
  quietButton,
  secondaryButton,
} from "@/components/styles";
import type { Dictionary } from "@/i18n/dictionaries/en";
import { type Locale, withLocale } from "@/i18n/locales";
import { api } from "@/lib/api/browser";
import { problemText } from "@/lib/api/problem";

/** Run the check, submit the application, edit it: whichever the user's role allows. */
export function ProjectActions({
  projectId,
  locale,
  canRun,
  canSubmit,
  canEdit,
  running,
  reading,
  hasDocuments,
  text,
  errors,
}: {
  projectId: number;
  locale: Locale;
  canRun: boolean;
  canSubmit: boolean;
  canEdit: boolean;
  running: boolean;
  reading: boolean;
  hasDocuments: boolean;
  text: Dictionary["workspace"] & { cancel: string };
  errors: Dictionary["errors"];
}) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [action, setAction] = useState<"run" | "submit" | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const path = { params: { path: { project_id: projectId } } };

  function act(
    kind: "run" | "submit",
    call: () => Promise<{ error?: unknown; response: Response }>,
    conflict: string,
  ) {
    setAction(kind);
    startTransition(async () => {
      try {
        const { error, response } = await call();
        setProblem(
          error
            ? problemText({ status: response.status, error }, errors, locale, {
                409: conflict,
              })
            : null,
        );
        if (!error) setConfirming(false);
      } catch {
        setProblem(errors.network);
      }
      router.refresh();
    });
  }

  const checking = running || (pending && action === "run");
  return (
    <div className="flex max-w-xl flex-col items-start gap-3 lg:items-end">
      <div className="flex flex-wrap items-center gap-3 lg:justify-end">
        {canEdit && (
          <Link
            href={withLocale(locale, `/projects/${projectId}/edit`)}
            className={quietButton}
          >
            {text.edit}
          </Link>
        )}
        {canSubmit && !confirming && (
          <button
            type="button"
            onClick={() => setConfirming(true)}
            disabled={pending}
            className={secondaryButton}
          >
            {text.submit}
          </button>
        )}
        {canRun && (
          <button
            type="button"
            onClick={() =>
              act(
                "run",
                () =>
                  api.POST("/api/projects/{project_id}/verifications", path),
                text.runConflict,
              )
            }
            disabled={pending || running || reading || !hasDocuments}
            className={primaryButton}
          >
            {checking ? text.runningCheck : text.runCheck}
          </button>
        )}
      </div>
      {confirming && (
        <div className="grid max-w-sm gap-3 lg:justify-items-end lg:text-right">
          <p className="text-sm text-ink">{text.submitConfirm}</p>
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => setConfirming(false)}
              disabled={pending}
              className={quietButton}
            >
              {text.cancel}
            </button>
            <button
              type="button"
              onClick={() =>
                act(
                  "submit",
                  () => api.POST("/api/projects/{project_id}/submit", path),
                  text.submitConflict,
                )
              }
              disabled={pending}
              className={primaryButton}
            >
              {pending && action === "submit"
                ? text.submitting
                : text.submitYes}
            </button>
          </div>
        </div>
      )}
      {problem && (
        <p role="alert" className="max-w-sm text-sm text-bad lg:text-right">
          {problem}
        </p>
      )}
    </div>
  );
}
