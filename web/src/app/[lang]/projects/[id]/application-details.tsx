import { Fragment } from "react";

import { sectionTitle } from "@/components/styles";
import type { Dictionary } from "@/i18n/dictionaries/en";

/** What the applicant declared; the CNP only ever appears masked. */
export function ApplicationDetails({
  form,
  dictionary,
}: {
  form: Record<string, unknown>;
  dictionary: Dictionary;
}) {
  const text = dictionary.application;
  const rows: [string, string][] = [
    [text.applicantName, "applicant_name"],
    [text.applicantCui, "applicant_cui"],
    [text.representativeName, "legal_representative_name"],
    [text.representativeCnp, "legal_representative_cnp_masked"],
    [text.requestedAmount, "requested_amount"],
    [text.iban, "iban"],
    [text.startDate, "start_date"],
    [text.endDate, "end_date"],
  ];
  return (
    <section className="panel mt-10" aria-labelledby="details-title">
      <h2 id="details-title" className={sectionTitle}>
        {dictionary.workspace.details}
      </h2>
      <dl className="application-details grid max-w-3xl gap-x-8 gap-y-3 sm:grid-cols-[16rem_1fr]">
        {rows.map(([label, key]) => {
          const value = form[key];
          return (
            <Fragment key={key}>
              <dt className="text-sm text-ink-2 sm:py-1">{label}</dt>
              <dd className="min-w-0 pb-3 text-sm font-medium tabular-nums sm:py-1">
                {typeof value === "string" && value ? (
                  value
                ) : (
                  <span className="text-ink-3">
                    {dictionary.workspace.notGiven}
                  </span>
                )}
              </dd>
            </Fragment>
          );
        })}
      </dl>
    </section>
  );
}
