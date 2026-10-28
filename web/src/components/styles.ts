// Class strings shared by every screen, taken from the status page (DESIGN.md: Buttons, Layout).

/** The single column every page uses (max 64rem, 20px gutters, 40px from 640px). */
export const pageColumn =
  "mx-auto w-full max-w-5xl px-5 py-10 sm:px-10 sm:py-16";

/** The action that does the work ("Run check"). Works on <button> and <a>. */
export const primaryButton =
  "inline-flex items-center rounded-md bg-accent px-4 py-2 text-sm font-semibold text-on-accent transition-colors duration-150 hover:bg-accent-hover disabled:cursor-progress disabled:opacity-70";

/** A second action beside the primary one (Upload, Submit for review). */
export const secondaryButton =
  "inline-flex items-center rounded-md border border-line-strong px-4 py-2 text-sm font-semibold text-ink transition-colors duration-150 hover:bg-surface-2 disabled:cursor-progress disabled:opacity-70";

/** Actions around the work (Edit, Delete, Sign out). */
export const quietButton =
  "inline-flex items-center rounded-md px-2.5 py-1.5 text-sm font-medium text-ink-2 transition-colors duration-150 hover:bg-surface-2 hover:text-ink disabled:cursor-progress disabled:opacity-70";

/** Text links inside content and tables. */
export const textLink =
  "font-medium text-accent underline decoration-line-strong underline-offset-[0.2em] transition-colors duration-150 hover:decoration-accent";

/** Text inputs, selects and textareas. */
export const fieldControl =
  "w-full rounded-md border border-line-strong bg-surface px-3 py-2 text-base text-ink transition-colors duration-150 placeholder:text-ink-3 hover:border-ink-3 disabled:cursor-not-allowed disabled:opacity-70 aria-invalid:border-bad";

/** Section heading spacing (48px between sections, DESIGN.md: Layout). */
export const sectionTitle = "mb-4 text-lg font-semibold tracking-tight";
