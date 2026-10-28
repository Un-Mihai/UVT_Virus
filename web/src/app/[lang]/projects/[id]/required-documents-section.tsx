import { StatusWord } from "@/components/status-word";
import { sectionTitle, textLink } from "@/components/styles";
import type { Dictionary } from "@/i18n/dictionaries/en";
import type { Locale } from "@/i18n/locales";
import { fill } from "@/i18n/template";
import type { components } from "@/lib/api/schema";

import { RequiredUpload } from "./required-upload";

type Item = components["schemas"]["RequiredDocumentOut"];
type Document = components["schemas"]["DocumentOut"];

/** Where an item comes from: an administrator, or the regulation page that requires it. */
function sourceOf(item: Item, text: Dictionary["required"]) {
  if (item.source === "admin") return text.setByAdmin;
  if (item.regulation_filename && item.regulation_page) {
    return fill(text.fromRegulation, {
      file: item.regulation_filename,
      page: item.regulation_page,
    });
  }
  return null;
}

/** The documents the applicant must add, each with what was uploaded for it. */
export function RequiredDocumentsSection({
  projectId,
  items,
  documents,
  editable,
  locale,
  dictionary,
}: {
  projectId: number;
  items: Item[];
  documents: Document[];
  editable: boolean;
  locale: Locale;
  dictionary: Dictionary;
}) {
  const text = dictionary.required;
  const filesFor = (item: Item) =>
    documents.filter((document) => document.required_document_id === item.id);
  const added = items.filter((item) => filesFor(item).length > 0).length;
  return (
    <section className="panel mt-10" aria-labelledby="required-title">
      <div className="mb-5 flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1">
        <h2 id="required-title" className={`${sectionTitle} mb-0`}>
          {text.title}
        </h2>
        {items.length > 0 && (
          <p className="text-ink-2 tabular-nums">
            {fill(text.progress, { added, total: items.length })}
          </p>
        )}
      </div>
      {items.length === 0 ? (
        <p className="max-w-prose text-ink-2">
          {editable ? text.empty : text.emptyReviewer}
        </p>
      ) : (
        <ul className="divide-y divide-line border-y border-line">
          {items.map((item) => {
            const files = filesFor(item);
            const source = sourceOf(item, text);
            return (
              <li
                key={item.id}
                className="flex flex-wrap items-start justify-between gap-x-6 gap-y-3 py-3.5"
              >
                <div className="grid min-w-0 gap-1.5">
                  <p className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                    <span className="font-medium">{item.name}</span>
                    <StatusWord state={files.length > 0 ? "ok" : "neutral"}>
                      {files.length > 0 ? text.added : text.notAdded}
                    </StatusWord>
                  </p>
                  {item.description && (
                    <p className="max-w-prose text-ink-2">{item.description}</p>
                  )}
                  {source && <p className="text-sm text-ink-3">{source}</p>}
                  {files.length > 0 && (
                    <ul className="grid gap-1 text-sm">
                      {files.map((file) => (
                        <li key={file.id}>
                          <a
                            href={`/api/projects/${projectId}/documents/${file.id}/file`}
                            target="_blank"
                            rel="noopener"
                            className={`${textLink} break-all`}
                          >
                            {file.filename}
                          </a>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
                {editable && (
                  <RequiredUpload
                    projectId={projectId}
                    itemId={item.id}
                    itemName={item.name}
                    locale={locale}
                    text={{
                      ...text,
                      failedUpload: dictionary.documents.failedUpload,
                    }}
                    errors={dictionary.errors}
                  />
                )}
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
