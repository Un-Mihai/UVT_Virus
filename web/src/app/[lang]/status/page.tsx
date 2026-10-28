import type { Metadata } from "next";
import { Suspense } from "react";

import { ConnectionCheck } from "./connection-check";
import { StatusReport, StatusReportSkeleton } from "./status-report";

export const metadata: Metadata = { title: "Stack status" };

export default function StatusPage() {
  return (
    // Developer diagnostics: written in English only, whatever the interface language.
    <main
      lang="en"
      className="mx-auto w-full max-w-5xl px-5 py-10 sm:px-10 sm:py-16"
    >
      <header className="grid gap-6 border-b border-line pb-8 lg:grid-cols-[1fr_auto] lg:gap-x-12">
        <div className="max-w-prose">
          <h1 className="text-2xl font-semibold tracking-tight text-balance">
            Stack status
          </h1>
          <p className="mt-2 text-ink-2">
            Web, API, database, AI provider and OCR for this project: the place
            to check the wiring when something in the product fails.
          </p>
        </div>
        <ConnectionCheck />
      </header>
      <Suspense fallback={<StatusReportSkeleton />}>
        <StatusReport />
      </Suspense>
    </main>
  );
}
