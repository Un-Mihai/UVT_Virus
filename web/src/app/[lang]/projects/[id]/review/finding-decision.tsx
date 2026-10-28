"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { StatusWord } from "@/components/status-word";
import { quietButton } from "@/components/styles";
import type { Dictionary } from "@/i18n/dictionaries/en";
import type { Locale } from "@/i18n/locales";
import { api } from "@/lib/api/browser";
import { problemText } from "@/lib/api/problem";

type Decision = "confirmed" | "dismissed";

/** People decide: confirm or dismiss a finding, or take the decision back. */
export function FindingDecision({
  findingId,
  decision,
  locale,
  text,
  errors,
}: {
  findingId: number;
  decision: Decision | null;
  locale: Locale;
  text: Dictionary["review"];
  errors: Dictionary["errors"];
}) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [problem, setProblem] = useState<string | null>(null);

  function decide(next: Decision | null) {
    startTransition(async () => {
      try {
        const { error, response } = await api.POST(
          "/api/findings/{finding_id}/decision",
          {
            params: { path: { finding_id: findingId } },
            body: { decision: next },
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
    <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1 px-3 pt-1">
      {decision ? (
        <>
          <StatusWord state={decision === "confirmed" ? "ok" : "neutral"}>
            {text[decision]}
          </StatusWord>
          <button
            type="button"
            disabled={pending}
            onClick={() => decide(null)}
            className={quietButton}
          >
            {pending ? text.deciding : text.undo}
          </button>
        </>
      ) : (
        <>
          <button
            type="button"
            disabled={pending}
            onClick={() => decide("confirmed")}
            className={quietButton}
          >
            {pending ? text.deciding : text.confirm}
          </button>
          <button
            type="button"
            disabled={pending}
            onClick={() => decide("dismissed")}
            className={quietButton}
          >
            {text.dismiss}
          </button>
        </>
      )}
      {problem && (
        <p role="alert" className="w-full text-sm text-bad">
          {problem}
        </p>
      )}
    </div>
  );
}
