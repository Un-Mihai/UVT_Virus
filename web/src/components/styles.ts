// Shared presentation classes (DESIGN.md: Buttons, Layout).

/** The single column every page uses (max 72rem, 20px gutters, 40px from 640px). */
export const pageColumn =
  "mx-auto w-full max-w-6xl px-5 py-10 sm:px-10 sm:py-14";

/** The action that does the work ("Run check"). Works on <button> and <a>. */
export const primaryButton =
  "inline-flex min-h-11 items-center justify-center gap-2 rounded-control bg-accent px-5 py-2.5 text-sm font-bold text-on-accent shadow-action transition-colors duration-150 hover:bg-accent-hover active:bg-accent-hover disabled:cursor-progress disabled:opacity-70 disabled:shadow-none";

/** A second action beside the primary one (Upload, Submit for review). */
export const secondaryButton =
  "inline-flex min-h-11 items-center justify-center gap-2 rounded-control border border-line-strong bg-surface px-5 py-2.5 text-sm font-semibold text-ink transition-colors duration-150 hover:border-ink hover:bg-surface-2 active:bg-surface-2 disabled:cursor-progress disabled:opacity-70";

/** Actions around the work (Edit, Delete, Sign out). */
export const quietButton =
  "inline-flex min-h-10 items-center justify-center rounded-control px-3 py-2 text-sm font-medium text-ink-2 transition-colors duration-150 hover:bg-surface-2 hover:text-ink active:bg-surface-2 disabled:cursor-progress disabled:opacity-70";

/** Text links inside content and tables. */
export const textLink =
  "rounded-sm font-semibold text-ink underline decoration-accent decoration-2 underline-offset-4 transition-colors duration-150 hover:decoration-ink";

/** Text inputs, selects and textareas. */
export const fieldControl =
  "min-h-12 w-full rounded-control border border-line-strong bg-surface px-3.5 py-2.5 text-base text-ink transition-colors duration-150 placeholder:text-ink-3 hover:border-ink-3 focus-visible:border-focus disabled:cursor-not-allowed disabled:opacity-70 aria-invalid:border-bad";

/** Section heading spacing (48px between sections, DESIGN.md: Layout). */
export const sectionTitle = "mb-5 text-xl font-bold tracking-tight";
