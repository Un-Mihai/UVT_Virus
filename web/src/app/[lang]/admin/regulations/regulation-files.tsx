"use client";

import { useRouter } from "next/navigation";
import { type ChangeEvent, useState, useTransition } from "react";

import { type StatusState, StatusWord } from "@/components/status-word";
import { quietButton, secondaryButton, textLink } from "@/components/styles";
import type { Dictionary } from "@/i18n/dictionaries/en";
import type { Locale } from "@/i18n/locales";
import { fill } from "@/i18n/template";
import { api } from "@/lib/api/browser";
import { problemText } from "@/lib/api/problem";
import type { components } from "@/lib/api/schema";
import { uploadRegulationDocument } from "@/lib/api/upload";
import { formatDateTime } from "@/lib/format";

type RegulationDocument = components["schemas"]["RegulationDocumentOut"];
type Text = Dictionary["admin"] & { cancel: string };

const OCR_STATES: Record<string, [StatusState, keyof Text]> = {
  pending: ["warn", "ocrReading"],
  done: ["ok", "ocrDone"],
  failed: ["bad", "ocrFailed"],
  unavailable: ["bad", "ocrUnavailable"],
};

/** The regulation PDFs of one rule set: AI-judged clauses quote them. */
export function RegulationFiles({
  documents,
  projectTypeId,
  scope,
  locale,
  text,
  errors,
}: {
  documents: RegulationDocument[];
  projectTypeId: number;
  scope: "client" | "reviewer";
  locale: Locale;
  text: Text;
  errors: Dictionary["errors"];
}) {
  const router = useRouter();
  const [uploading, setUploading] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);

  async function upload(event: ChangeEvent<HTMLInputElement>) {
    const input = event.currentTarget;
    const file = input.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const { error, response } = await uploadRegulationDocument(
        projectTypeId,
        scope,
        file,
      );
      setProblem(
        error
          ? problemText({ status: response.status, error }, errors, locale)
          : null,
      );
    } catch {
      setProblem(errors.network);
    }
    input.value = "";
    setUploading(false);
    router.refresh();
  }

  return (
    <>
      {documents.length === 0 ? (
        <p className="max-w-prose text-ink-2">{text.noDocuments}</p>
      ) : (
        <ul className="divide-y divide-line border-y border-line">
          {documents.map((document) => (
            <FileRow
              key={document.id}
              document={document}
              locale={locale}
              text={text}
              errors={errors}
            />
          ))}
        </ul>
      )}
      <div className="mt-6 grid justify-items-start gap-2">
        <label
          className={`${secondaryButton} cursor-pointer has-focus-visible:outline-2 has-focus-visible:outline-offset-2 has-focus-visible:outline-accent has-disabled:cursor-progress has-disabled:opacity-70`}
        >
          {uploading ? text.uploading : text.uploadDocument}
          <input
            type="file"
            accept="application/pdf"
            disabled={uploading}
            onChange={upload}
            className="sr-only"
          />
        </label>
        <p aria-live="polite" className="text-sm text-bad">
          {problem}
        </p>
      </div>
    </>
  );
}

function FileRow({
  document,
  locale,
  text,
  errors,
}: {
  document: RegulationDocument;
  locale: Locale;
  text: Text;
  errors: Dictionary["errors"];
}) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [confirming, setConfirming] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const path = { params: { path: { document_id: document.id } } };
  const ocr = document.ocr_status ? OCR_STATES[document.ocr_status] : undefined;

  function act(call: () => Promise<{ error?: unknown; response: Response }>) {
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
    <li className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-2 py-3.5">
      <div className="grid gap-1">
        <a
          href={`/api/regulation-documents/${document.id}/file`}
          target="_blank"
          rel="noopener"
          className={`${textLink} break-all`}
        >
          {document.filename}
        </a>
        <p className="flex flex-wrap items-baseline gap-x-3 gap-y-1 text-sm text-ink-2">
          <span>
            {fill(text.uploadedAt, {
              date: formatDateTime(document.created_at, locale),
            })}
          </span>
          {ocr && (
            <StatusWord state={ocr[0]}>{String(text[ocr[1]])}</StatusWord>
          )}
        </p>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        {document.ocr_status === "failed" && (
          <button
            type="button"
            disabled={pending}
            onClick={() =>
              act(() =>
                api.POST(
                  "/api/regulation-documents/{document_id}/read-scans",
                  path,
                ),
              )
            }
            className={quietButton}
          >
            {pending ? text.readingAgain : text.readAgain}
          </button>
        )}
        {confirming ? (
          <>
            <button
              type="button"
              disabled={pending}
              onClick={() =>
                act(() =>
                  api.DELETE("/api/regulation-documents/{document_id}", path),
                )
              }
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
              {text.cancel}
            </button>
          </>
        ) : (
          <button
            type="button"
            onClick={() => setConfirming(true)}
            className={quietButton}
          >
            {text.remove}
          </button>
        )}
      </div>
      {problem && (
        <p role="alert" className="w-full text-sm text-bad">
          {problem}
        </p>
      )}
    </li>
  );
}
