"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { api } from "@/lib/api/browser";

type Outcome = { ok: true; text: string } | { ok: false; text: string };

export function ConnectionCheck() {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [outcome, setOutcome] = useState<Outcome | null>(null);

  function run() {
    startTransition(async () => {
      const { data, error, response } = await api.POST("/api/ai/check");
      if (data) {
        setOutcome({
          ok: true,
          text: data.embedding_model
            ? `${data.chat_model} answered and ${data.embedding_model} returned ${data.embedding_dimensions} dimensions.`
            : `${data.chat_model} answered. This provider has no embeddings endpoint, so no embedding was checked.`,
        });
      } else {
        setOutcome({
          ok: false,
          text: error?.detail ?? `The API answered ${response.status}.`,
        });
      }
      router.refresh();
    });
  }

  return (
    <div className="flex max-w-sm flex-col items-start gap-3 lg:items-end">
      <button
        type="button"
        onClick={run}
        disabled={pending}
        className="inline-flex min-h-11 items-center justify-center gap-2 rounded-control bg-accent px-5 py-2.5 text-sm font-bold text-on-accent shadow-action transition-colors duration-150 hover:bg-accent-hover active:bg-accent-hover disabled:cursor-progress disabled:opacity-70 disabled:shadow-none"
      >
        {pending ? "Checking…" : "Run AI check"}
      </button>
      <p
        aria-live="polite"
        className={`text-sm lg:text-right ${outcome?.ok === false ? "text-bad" : "text-ink-2"}`}
      >
        {outcome?.text ?? "Sends one tiny chat request and one embedding."}
      </p>
    </div>
  );
}
