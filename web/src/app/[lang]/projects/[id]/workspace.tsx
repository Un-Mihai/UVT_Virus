import { notFound } from "next/navigation";

import { PageHeader } from "@/components/page-header";
import { RefreshWhile } from "@/components/refresh-while";
import { type StatusState, StatusWord } from "@/components/status-word";
import { sectionTitle } from "@/components/styles";
import type { Dictionary } from "@/i18n/dictionaries/en";
import { currentLocale, getDictionary } from "@/i18n/dictionary";
import type { Locale } from "@/i18n/locales";
import { fill, plural } from "@/i18n/template";
import type { components } from "@/lib/api/schema";
import { api } from "@/lib/api/server";
import { currentUser } from "@/lib/auth/current-user";
import { formatDateTime, formatPercent } from "@/lib/format";
import { hasRole } from "@/lib/roles";

import { ApplicationDetails } from "./application-details";
import { DocumentsSection } from "./documents-section";
import { ProjectActions } from "./project-actions";
import { ReviewPane } from "./review/review-pane";

type Run = components["schemas"]["RunOut"];
type Document = components["schemas"]["DocumentOut"];

async function load(projectId: number) {
  const path = { params: { path: { project_id: projectId } } };
  try {
    const [project, report, types] = await Promise.all([
      api.GET("/api/projects/{project_id}", path),
      api.GET("/api/projects/{project_id}/verifications/latest", path),
      api.GET("/api/project-types"),
    ]);
    return {
      reachable: true,
      project: project.data,
      report: report.data,
      types: types.data ?? [],
    };
  } catch {
    return {
      reachable: false,
      project: undefined,
      report: undefined,
      types: [],
    };
  }
}

/** Whether OCR is still reading some scanned page (and has not stalled). */
function isReading(documents: Document[]) {
  return documents.some(
    (document) =>
      !document.reading_stalled &&
      document.pages.some((page) => page.ocr_status === "pending"),
  );
}

/** One project: its check, its documents with the findings beside them, and its form. */
export async function Workspace({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const projectId = Number((await params).id);
  if (!Number.isInteger(projectId)) notFound();
  const [dictionary, locale, user, loaded] = await Promise.all([
    getDictionary(),
    currentLocale(),
    currentUser(),
    load(projectId),
  ]);
  if (!loaded.reachable) {
    return (
      <p role="alert" className="max-w-prose text-bad">
        {dictionary.common.apiUnreachable}
      </p>
    );
  }
  const { project, report, types } = loaded;
  if (!project) notFound();

  const text = dictionary.workspace;
  const isOwner = hasRole(user, "client") && project.owner_id === user?.id;
  const isReviewer = hasRole(user, "reviewer");
  const draft = project.status === "draft";
  const run = report?.run ?? null;
  const running = run?.status === "pending" || run?.status === "running";
  const reading = isReading(project.documents);
  const typeName =
    types.find((type) => type.id === project.project_type_id)?.name ?? "";
  const completed = run?.status === "completed" ? report : null;

  return (
    <>
      <RefreshWhile active={running || reading} />
      <PageHeader
        title={project.title}
        lead={fill(text.typeAndStatus, {
          type: typeName,
          status: dictionary.projectStatus[project.status],
        })}
        actions={
          <ProjectActions
            projectId={project.id}
            locale={locale}
            canRun={isOwner || (isReviewer && !draft)}
            canSubmit={isOwner && draft}
            canEdit={isOwner && draft}
            running={running}
            reading={reading}
            hasDocuments={project.documents.length > 0}
            text={{ ...text, cancel: dictionary.form.cancel }}
            errors={dictionary.errors}
          />
        }
      />
      <CheckState
        run={run}
        reading={reading}
        scope={isReviewer ? text.reviewerCheck : text.clientCheck}
        text={text}
        locale={locale}
      />
      <DocumentsSection
        projectId={project.id}
        documents={project.documents}
        editable={isOwner && draft}
        locale={locale}
        dictionary={dictionary}
      />
      <section className="mt-12" aria-labelledby="findings-title">
        <h2 id="findings-title" className={sectionTitle}>
          {dictionary.review.title}
        </h2>
        {project.documents.length === 0 ? (
          <p className="max-w-prose text-ink-2">
            {dictionary.review.noDocuments}
          </p>
        ) : (
          <ReviewPane
            projectId={project.id}
            locale={locale}
            documents={project.documents.map(({ id, filename, pages }) => ({
              id,
              filename,
              pages: pages.map(({ number, width, height }) => ({
                number,
                width,
                height,
              })),
            }))}
            findings={completed?.findings ?? []}
            note={
              completed
                ? summary(
                    completed.findings.length,
                    completed.min_confidence,
                    locale,
                    dictionary,
                  )
                : running
                  ? text.running
                  : run?.status === "failed"
                    ? text.failed
                    : text.neverRun
            }
            canDecide={isOwner || isReviewer}
            text={{
              ...dictionary.review,
              severity: dictionary.severity,
              errors: dictionary.errors,
              page: dictionary.common.page,
            }}
          />
        )}
      </section>
      <ApplicationDetails form={project.form} dictionary={dictionary} />
    </>
  );
}

function summary(
  count: number,
  threshold: number,
  locale: Locale,
  dictionary: Dictionary,
) {
  const values = { threshold: formatPercent(threshold, locale) };
  if (count === 0) return fill(dictionary.review.none, values);
  return fill(plural(locale, count, dictionary.review.summary), values);
}

/** Where the caller's check stands, in one line that says what happens next. */
function CheckState({
  run,
  reading,
  scope,
  text,
  locale,
}: {
  run: Run | null;
  reading: boolean;
  scope: string;
  text: Dictionary["workspace"];
  locale: Locale;
}) {
  let state: StatusState = "neutral";
  let message = text.neverRun;
  if (reading) {
    [state, message] = ["warn", text.readingBlocks];
  } else if (run?.status === "pending" || run?.status === "running") {
    [state, message] = ["warn", text.running];
  } else if (run?.status === "failed") {
    [state, message] = ["bad", text.failed];
  } else if (run?.status === "completed") {
    const date = formatDateTime(run.finished_at ?? run.created_at, locale);
    [state, message] = ["ok", fill(text.lastRun, { date })];
  }
  return (
    <div
      aria-live="polite"
      className="mt-8 flex flex-wrap items-baseline gap-x-3 gap-y-1"
    >
      <StatusWord state={state}>{scope}</StatusWord>
      <p className="max-w-prose text-ink-2">{message}</p>
      {run?.status === "failed" && run.error && (
        <code className="text-sm text-ink-3">{run.error}</code>
      )}
    </div>
  );
}
