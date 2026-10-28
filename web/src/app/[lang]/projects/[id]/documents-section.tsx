import { type StatusState, StatusWord } from "@/components/status-word";
import { sectionTitle, textLink } from "@/components/styles";
import type { Dictionary } from "@/i18n/dictionaries/en";
import type { Locale } from "@/i18n/locales";
import { fill, plural } from "@/i18n/template";
import type { components } from "@/lib/api/schema";

import { DocumentActions } from "./document-actions";
import { DocumentUpload } from "./document-upload";

type Document = components["schemas"]["DocumentOut"];

/** How OCR is doing on a document's scanned pages, as one state and one sentence. */
function readingState(
  document: Document,
  text: Dictionary["documents"],
  locale: Locale,
): { state: StatusState; label: string; readAgain: boolean } | null {
  const scanned = document.pages.filter((page) => page.ocr_status !== null);
  if (scanned.length === 0) return null;
  const count = (status: string) =>
    scanned.filter((page) => page.ocr_status === status).length;
  const done = count("done");
  if (count("pending") > 0) {
    return document.reading_stalled
      ? { state: "warn", label: text.stalled, readAgain: true }
      : {
          state: "warn",
          label: fill(text.reading, { done, total: scanned.length }),
          readAgain: false,
        };
  }
  const unreadable = count("failed") + count("unavailable");
  if (unreadable > 0) {
    return {
      state: "bad",
      label: plural(locale, unreadable, text.unreadable),
      readAgain: count("failed") > 0,
    };
  }
  return {
    state: "ok",
    label: plural(locale, done, text.readByOcr),
    readAgain: false,
  };
}

/** What the latest finished check found in a document; null counts mean no check has finished. */
function checkState(
  counts: { total: number; open: number } | undefined,
  checked: boolean,
  checking: boolean,
  text: Dictionary["documents"],
  locale: Locale,
): { state: StatusState; label: string } {
  if (checking) return { state: "warn", label: text.checking };
  if (!checked) return { state: "neutral", label: text.notChecked };
  const { total, open } = counts ?? { total: 0, open: 0 };
  if (total === 0) return { state: "ok", label: text.noFindings };
  if (open === 0) return { state: "ok", label: text.allDecided };
  return { state: "warn", label: plural(locale, open, text.openFindings) };
}

export function DocumentsSection({
  projectId,
  documents,
  checks,
  checking,
  editable,
  locale,
  dictionary,
}: {
  projectId: number;
  documents: Document[];
  /** Findings per document id from the latest finished check; null before one has finished. */
  checks: Record<number, { total: number; open: number }> | null;
  checking: boolean;
  editable: boolean;
  locale: Locale;
  dictionary: Dictionary;
}) {
  const text = dictionary.documents;
  return (
    <section className="panel mt-10" aria-labelledby="documents-title">
      <h2 id="documents-title" className={sectionTitle}>
        {text.title}
      </h2>
      {documents.length === 0 ? (
        <p className="max-w-prose text-ink-2">
          {editable ? text.empty : text.emptyReviewer}
        </p>
      ) : (
        <ul className="divide-y divide-line border-y border-line">
          {documents.map((document) => {
            const reading = readingState(document, text, locale);
            const check = checkState(
              checks?.[document.id],
              checks !== null,
              checking,
              text,
              locale,
            );
            const type = document.document_type as
              keyof Dictionary["documentTypes"] | null;
            return (
              <li
                key={document.id}
                className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-2 py-3.5"
              >
                <div className="grid min-w-0 gap-1.5">
                  <a
                    href={`/api/projects/${projectId}/documents/${document.id}/file`}
                    target="_blank"
                    rel="noopener"
                    className={`${textLink} break-all`}
                  >
                    {document.filename}
                  </a>
                  <p className="flex flex-wrap items-baseline gap-x-3 gap-y-1 text-sm text-ink-2">
                    {type && dictionary.documentTypes[type] && (
                      <span>{dictionary.documentTypes[type]}</span>
                    )}
                    <span className="tabular-nums">
                      {plural(locale, document.page_count, text.pages)}
                    </span>
                    {reading && (
                      <StatusWord state={reading.state}>
                        {reading.label}
                      </StatusWord>
                    )}
                    <StatusWord state={check.state}>{check.label}</StatusWord>
                  </p>
                </div>
                <DocumentActions
                  projectId={projectId}
                  documentId={document.id}
                  filename={document.filename}
                  canReadAgain={reading?.readAgain ?? false}
                  canDelete={editable}
                  locale={locale}
                  text={{ ...text, cancel: dictionary.form.cancel }}
                  errors={dictionary.errors}
                />
              </li>
            );
          })}
        </ul>
      )}
      {editable && (
        <DocumentUpload
          projectId={projectId}
          locale={locale}
          text={text}
          errors={dictionary.errors}
        />
      )}
    </section>
  );
}
