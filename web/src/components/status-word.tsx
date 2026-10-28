import type { ReactNode } from "react";

export type StatusState = "ok" | "warn" | "bad" | "neutral";

const dot: Record<StatusState, string> = {
  ok: "bg-ok",
  warn: "bg-warn",
  bad: "bg-bad",
  neutral: "bg-line-strong",
};

const word: Record<StatusState, string> = {
  ok: "text-ink-2",
  warn: "text-warn",
  bad: "text-bad",
  neutral: "text-ink-2",
};

/** A state as dot plus word: colour is never the only signal (DESIGN.md: State-Only Colour). */
export function StatusWord({
  state,
  children,
}: {
  state: StatusState;
  children: ReactNode;
}) {
  return (
    <span
      className={`inline-flex items-baseline gap-2 text-sm font-medium whitespace-nowrap ${word[state]}`}
    >
      <span
        aria-hidden
        className={`size-2 shrink-0 translate-y-[-0.1em] rounded-full ${dot[state]}`}
      />
      {children}
    </span>
  );
}
