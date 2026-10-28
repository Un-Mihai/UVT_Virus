"use client";

import { useRouter } from "next/navigation";
import { type ChangeEvent, useState } from "react";

import { secondaryButton } from "@/components/styles";
import type { Dictionary } from "@/i18n/dictionaries/en";
import type { Locale } from "@/i18n/locales";
import { fill } from "@/i18n/template";
import { problemText } from "@/lib/api/problem";
import { uploadProjectDocument } from "@/lib/api/upload";

/** Uploads one PDF for an item of the list of documents to add. */
export function RequiredUpload({
  projectId,
  itemId,
  itemName,
  locale,
  text,
  errors,
}: {
  projectId: number;
  itemId: number;
  itemName: string;
  locale: Locale;
  text: Dictionary["required"] & { failedUpload: string };
  errors: Dictionary["errors"];
}) {
  const router = useRouter();
  const [uploading, setUploading] = useState<string | null>(null);
  const [problem, setProblem] = useState<string | null>(null);

  async function upload(event: ChangeEvent<HTMLInputElement>) {
    const input = event.currentTarget;
    const file = input.files?.[0];
    if (!file) return;
    setUploading(file.name);
    setProblem(null);
    const failed = (reason: string) =>
      fill(text.failedUpload, { name: file.name, reason });
    try {
      const { error, response } = await uploadProjectDocument(
        projectId,
        file,
        itemId,
      );
      if (error) {
        setProblem(
          failed(
            problemText({ status: response.status, error }, errors, locale),
          ),
        );
      }
    } catch {
      setProblem(failed(errors.network));
    }
    input.value = "";
    setUploading(null);
    router.refresh();
  }

  return (
    <div className="grid justify-items-start gap-2">
      <label
        className={`${secondaryButton} cursor-pointer has-focus-visible:outline-2 has-focus-visible:outline-offset-2 has-focus-visible:outline-focus has-disabled:cursor-progress has-disabled:opacity-70`}
      >
        {uploading ? fill(text.uploading, { name: uploading }) : text.upload}
        <span className="sr-only">: {itemName}</span>
        <input
          type="file"
          accept="application/pdf"
          disabled={uploading !== null}
          onChange={upload}
          className="sr-only"
        />
      </label>
      {problem && (
        <p role="alert" className="text-sm text-bad">
          {problem}
        </p>
      )}
    </div>
  );
}
