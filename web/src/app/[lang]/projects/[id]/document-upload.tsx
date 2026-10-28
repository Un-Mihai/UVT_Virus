"use client";

import { useRouter } from "next/navigation";
import { type ChangeEvent, useState } from "react";

import { secondaryButton } from "@/components/styles";
import type { Dictionary } from "@/i18n/dictionaries/en";
import type { Locale } from "@/i18n/locales";
import { fill } from "@/i18n/template";
import { problemText } from "@/lib/api/problem";
import { uploadProjectDocument } from "@/lib/api/upload";

type Outcome = { name: string; ok: boolean; text: string };

/** Uploads PDFs one after another and says how each went. */
export function DocumentUpload({
  projectId,
  locale,
  text,
  errors,
}: {
  projectId: number;
  locale: Locale;
  text: Dictionary["documents"];
  errors: Dictionary["errors"];
}) {
  const router = useRouter();
  const [uploading, setUploading] = useState<string | null>(null);
  const [outcomes, setOutcomes] = useState<Outcome[]>([]);

  async function upload(event: ChangeEvent<HTMLInputElement>) {
    const input = event.currentTarget;
    const files = Array.from(input.files ?? []);
    const results: Outcome[] = [];
    for (const file of files) {
      setUploading(file.name);
      try {
        const { error, response } = await uploadProjectDocument(
          projectId,
          file,
        );
        results.push(
          error
            ? {
                name: file.name,
                ok: false,
                text: fill(text.failedUpload, {
                  name: file.name,
                  reason: problemText(
                    { status: response.status, error },
                    errors,
                    locale,
                  ),
                }),
              }
            : {
                name: file.name,
                ok: true,
                text: fill(text.uploaded, { name: file.name }),
              },
        );
      } catch {
        results.push({
          name: file.name,
          ok: false,
          text: fill(text.failedUpload, {
            name: file.name,
            reason: errors.network,
          }),
        });
      }
    }
    input.value = "";
    setUploading(null);
    setOutcomes(results);
    router.refresh();
  }

  return (
    <div className="mt-6 grid gap-3">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <label
          className={`${secondaryButton} cursor-pointer has-focus-visible:outline-2 has-focus-visible:outline-offset-2 has-focus-visible:outline-accent has-disabled:cursor-progress has-disabled:opacity-70`}
        >
          {uploading ? fill(text.uploading, { name: uploading }) : text.upload}
          <input
            type="file"
            accept="application/pdf"
            multiple
            disabled={uploading !== null}
            onChange={upload}
            className="sr-only"
          />
        </label>
        <p className="max-w-prose text-sm text-ink-2">{text.uploadHint}</p>
      </div>
      <ul aria-live="polite" className="grid gap-1 text-sm">
        {outcomes.map((outcome) => (
          <li
            key={outcome.name}
            className={outcome.ok ? "text-ink-2" : "text-bad"}
          >
            {outcome.text}
          </li>
        ))}
      </ul>
    </div>
  );
}
