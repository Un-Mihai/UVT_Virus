import Link from "next/link";
import { notFound } from "next/navigation";

import { PageHeader } from "@/components/page-header";
import { RefreshWhile } from "@/components/refresh-while";
import { type StatusState, StatusWord } from "@/components/status-word";
import { sectionTitle, textLink } from "@/components/styles";
import type { Dictionary } from "@/i18n/dictionaries/en";
import { currentLocale, getDictionary } from "@/i18n/dictionary";
import { type Locale, withLocale } from "@/i18n/locales";
import { fill, plural } from "@/i18n/template";
import type { components } from "@/lib/api/schema";
import { api } from "@/lib/api/server";
import { currentUser } from "@/lib/auth/current-user";
import { applicantOf, fileState } from "@/lib/file-state";
import { formatDateTime, formatPercent } from "@/lib/format";
import { hasRole } from "@/lib/roles";

import { ApplicationDetails } from "./application-details";
import { DocumentsSection } from "./documents-section";
import { ProjectActions } from "./project-actions";
import { RequiredDocumentsSection } from "./required-documents-section";
import { ReviewPane } from "./review/review-pane";
import { VerdictForm } from "./verdict-form";

type Run = components["schemas"]["RunOut"];
type Document = components["schemas"]["DocumentOut"];
type Finding = components["schemas"]["FindingOut"];
type Project = components["schemas"]["ProjectOut"];

async function load(projectId: number) {
  const path = { params: { path: { project_id: projectId } } };
  try {
    const [project, report, types, required] = await Promise.all([
      api.GET("/api/projects/{project_id}", path),
      api.GET("/api/projects/{project_id}/verifications/latest", path),
      api.GET("/api/project-types"),
      api.GET("/api/projects/{project_id}/required-documents", path),
    ]);
    return {
      reachable: true,
      project: project.data,
      report: report.data,
      types: types.data ?? [],
      required: required.data ?? [],
    };
  } catch {
    return {
      reachable: false,
      project: undefined,
      report: undefined,
      types: [],
      required: [],
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

/** Per document: how many findings the latest finished check has, and how many still lack a decision. */
function countFindings(findings: Finding[]) {
  const counts: Record<number, { total: number; open: number }> = {};
  for (const { document_id, decision } of findings) {
    if (document_id === null) continue;
    const count = (counts[document_id] ??= { total: 0, open: 0 });
    count.total += 1;
    if (decision === null) count.open += 1;
  }
  return counts;
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
  const { project, report, types, required } = loaded;
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
  // A file missing a required document is reported and nothing else is checked, so its
  // documents must not read as checked (the rule code is the API's, completeness agent).
  const incomplete =
    completed?.findings.some(
      (finding) =>
        finding.rule_code === "completeness.required_document_missing",
    ) ?? false;
  const file = fileState(project);
  const applicant = applicantOf(project, dictionary.common.unnamedApplicant);
  const status = dictionary.fileState[file.key];

  return (
    <>
      {/* Fast while work runs; slowly while the applicant waits for a reviewer's move or verdict. */}
      <RefreshWhile
        active={
          running ||
          reading ||
          (isOwner && (file.key === "waiting" || file.key === "inReview"))
        }
        every={running || reading ? 2500 : 15000}
      />
      {isReviewer && (
        <Link
          href={withLocale(locale, "/")}
          className={`${textLink} mb-6 inline-block`}
        >
          ← {text.backToApplicants}
        </Link>
      )}
      <PageHeader
        title={project.title}
        lead={
          isReviewer
            ? fill(text.applicantTypeAndStatus, {
                applicant: applicant.name,
                type: typeName,
                status,
              })
            : fill(text.typeAndStatus, { type: typeName, status })
        }
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
      <div className="mt-8 grid gap-3">
        {isOwner && (
          <FileState
            file={file}
            project={project}
            dictionary={dictionary}
            locale={locale}
          />
        )}
        <CheckState
          run={run}
          reading={reading}
          scope={isReviewer ? text.reviewerCheck : text.clientCheck}
          text={text}
          locale={locale}
        />
      </div>
      <RequiredDocumentsSection
        projectId={project.id}
        items={required}
        documents={project.documents}
        editable={isOwner && draft}
        locale={locale}
        dictionary={dictionary}
      />
      <DocumentsSection
        projectId={project.id}
        documents={project.documents}
        items={required}
        checks={
          completed && !incomplete ? countFindings(completed.findings) : null
        }
        checking={running}
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
      {isReviewer && !draft && (
        <section className="panel mt-12" aria-labelledby="verdict-title">
          <h2 id="verdict-title" className={sectionTitle}>
            {dictionary.verdict.title}
          </h2>
          <p className="mb-4 max-w-prose text-ink-2">
            {project.verdict === "approved" && project.verdict_at
              ? fill(dictionary.verdict.approvedOn, {
                  date: formatDateTime(project.verdict_at, locale),
                })
              : dictionary.verdict.lead}
          </p>
          <VerdictForm
            projectId={project.id}
            locale={locale}
            initialNote={project.verdict_note ?? ""}
            text={dictionary.verdict}
            errors={dictionary.errors}
          />
        </section>
      )}
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
      className="flex flex-wrap items-baseline gap-x-3 gap-y-1"
    >
      <StatusWord state={state}>{scope}</StatusWord>
      <p className="max-w-prose text-ink-2">{message}</p>
      {run?.status === "failed" && run.error && (
        <code className="text-sm text-ink-3">{run.error}</code>
      )}
    </div>
  );
}

/** Where the applicant's file stands, with what happens next. */
function FileState({
  file,
  project,
  dictionary,
  locale,
}: {
  file: ReturnType<typeof fileState>;
  project: Pick<Project, "submitted_at" | "verdict_at" | "verdict_note">;
  dictionary: Dictionary;
  locale: Locale;
}) {
  const text = dictionary.fileState;
  const when = (date: string | null) =>
    date ? formatDateTime(date, locale) : "";
  const note = {
    draft: text.draftNote,
    waiting: fill(text.waitingNote, { date: when(project.submitted_at) }),
    inReview: text.inReviewNote,
    approved: fill(text.approvedNote, { date: when(project.verdict_at) }),
    changesRequested: text.changesRequestedNote,
  }[file.key];
  return (
    <div
      aria-live="polite"
      className="flex flex-wrap items-baseline gap-x-3 gap-y-1"
    >
      <StatusWord state={file.state}>{text[file.key]}</StatusWord>
      <p className="max-w-prose text-ink-2">{note}</p>
      {project.verdict_note && (
        <p className="w-full max-w-prose text-ink">
          <span className="font-semibold">{text.reviewerNote}</span>{" "}
          {project.verdict_note}
        </p>
      )}
    </div>
  );
}
