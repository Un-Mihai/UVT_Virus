"use client";

import { useState } from "react";

import {
  DocumentViewer,
  type JumpRequest,
  type ViewerHighlight,
  type ViewerPage,
} from "@/components/document-viewer";
import { StatusWord } from "@/components/status-word";
import { textLink } from "@/components/styles";
import type { Dictionary } from "@/i18n/dictionaries/en";
import type { Locale } from "@/i18n/locales";
import { fill } from "@/i18n/template";
import type { components } from "@/lib/api/schema";
import { formatPercent } from "@/lib/format";

import { FindingDecision } from "./finding-decision";

type Finding = components["schemas"]["FindingOut"];
type Text = Dictionary["review"] & {
  severity: Dictionary["severity"];
  errors: Dictionary["errors"];
  page: string;
};

const paneScroll = "lg:max-h-[calc(100dvh-6rem)] lg:overflow-y-auto";

/** The two-pane ledger split: the findings on the left, the highlighted document on the right.
 *  Choosing a finding shows its document, scrolls to the passage and moves focus there. */
export function ReviewPane({
  projectId,
  locale,
  documents,
  findings,
  note,
  canDecide,
  text,
}: {
  projectId: number;
  locale: Locale;
  documents: { id: number; filename: string; pages: ViewerPage[] }[];
  findings: Finding[];
  /** What the list shows: how many findings and at which threshold, or why there are none. */
  note: string;
  canDecide: boolean;
  text: Text;
}) {
  const firstWithFinding = findings.find(
    (finding) => finding.document_id,
  )?.document_id;
  const [documentId, setDocumentId] = useState(
    firstWithFinding ?? documents[0]?.id,
  );
  const [activeId, setActiveId] = useState<number | null>(null);
  const [jump, setJump] = useState<JumpRequest>(null);
  const document =
    documents.find((candidate) => candidate.id === documentId) ?? documents[0];

  const localized = (value: Record<string, string>) =>
    value[locale] ?? value.en ?? "";
  const select = (finding: Finding) => {
    setActiveId(finding.id);
    if (finding.document_id === null) return;
    setDocumentId(finding.document_id);
    setJump({ id: finding.id });
  };
  const highlights: ViewerHighlight[] = findings
    .filter((finding) => finding.document_id === document?.id && finding.page)
    .map((finding) => ({
      id: finding.id,
      page: finding.page ?? 1,
      rects: finding.rects,
      severity: finding.severity,
      label: `${text.severity[finding.severity]}: ${localized(finding.reason)}`,
      note: (
        <>
          <StatusWord state={finding.severity}>
            {text.severity[finding.severity]}
          </StatusWord>
          <p className="mt-1">{localized(finding.reason)}</p>
          <p className="mt-1 text-ink-2">
            <span className="font-medium text-ink">{text.recommendation}</span>{" "}
            {localized(finding.recommendation)}
          </p>
        </>
      ),
    }));

  return (
    <div className="grid gap-8 lg:grid-cols-[minmax(20rem,26rem)_1fr]">
      <div className={paneScroll}>
        <p className="mb-4 max-w-prose text-ink-2">{note}</p>
        {findings.length > 0 && (
          <ol className="divide-y divide-line border-y border-line">
            {findings.map((finding) => (
              <li key={finding.id} className="py-2">
                <button
                  type="button"
                  aria-current={finding.id === activeId || undefined}
                  onClick={() => select(finding)}
                  className="block w-full rounded-md px-3 py-2 text-left transition-colors duration-150 hover:bg-surface-2 aria-current:bg-surface-2"
                >
                  <span className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                    <StatusWord state={finding.severity}>
                      {text.severity[finding.severity]}
                    </StatusWord>
                    <span className="text-sm text-ink-2 tabular-nums">
                      {fill(text.confidence, {
                        value: formatPercent(finding.confidence, locale),
                      })}
                    </span>
                    {finding.ocr && (
                      <span className="text-sm text-ink-2">
                        {text.readByOcr}
                      </span>
                    )}
                  </span>
                  <span className="mt-1 block text-sm text-ink-3">
                    {finding.document_name && finding.page
                      ? fill(text.location, {
                          document: finding.document_name,
                          page: finding.page,
                        })
                      : text.noLocation}
                  </span>
                  {finding.quote && (
                    <q className="mt-2 block text-ink">{finding.quote}</q>
                  )}
                  <span className="mt-2 block">
                    {localized(finding.reason)}
                  </span>
                  <span className="mt-1 block text-ink-2">
                    <span className="font-medium text-ink">
                      {text.recommendation}
                    </span>{" "}
                    {localized(finding.recommendation)}
                  </span>
                </button>
                {canDecide && (
                  <FindingDecision
                    findingId={finding.id}
                    decision={finding.decision}
                    locale={locale}
                    text={text}
                    errors={text.errors}
                  />
                )}
              </li>
            ))}
          </ol>
        )}
      </div>
      {document && (
        <div className={`grid content-start gap-4 ${paneScroll}`}>
          <div className="flex flex-wrap items-center justify-between gap-3">
            {documents.length > 1 ? (
              <div
                role="group"
                aria-label={text.viewer}
                className="flex flex-wrap gap-1"
              >
                {documents.map((candidate) => (
                  <button
                    key={candidate.id}
                    type="button"
                    aria-pressed={candidate.id === document.id}
                    onClick={() => setDocumentId(candidate.id)}
                    className="rounded-md px-2.5 py-1.5 text-sm font-medium text-ink-2 transition-colors duration-150 hover:bg-surface-2 hover:text-ink aria-pressed:bg-surface-2 aria-pressed:text-ink"
                  >
                    {candidate.filename}
                  </button>
                ))}
              </div>
            ) : (
              <p className="text-sm font-medium text-ink">
                {document.filename}
              </p>
            )}
            <a
              href={`/api/projects/${projectId}/documents/${document.id}/annotated?lang=${locale}`}
              className={`${textLink} text-sm`}
            >
              {text.annotated}
            </a>
          </div>
          <DocumentViewer
            key={document.id}
            url={`/api/projects/${projectId}/documents/${document.id}/file`}
            pages={document.pages}
            highlights={highlights}
            activeId={activeId}
            jump={jump}
            onSelect={(id) =>
              setActiveId((current) => (current === id ? null : id))
            }
            text={{
              loading: text.loadingDocument,
              failed: text.documentFailed,
              page: text.page,
            }}
          />
        </div>
      )}
    </div>
  );
}
