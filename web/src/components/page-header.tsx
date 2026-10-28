import type { ReactNode } from "react";

/** One headline per page with its lead; actions sit beside it from 1024px, below it before. */
export function PageHeader({
  title,
  lead,
  actions,
}: {
  title: ReactNode;
  lead?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <header className="grid gap-6 border-b border-line pb-8 lg:grid-cols-[1fr_auto] lg:gap-x-12">
      <div className="max-w-prose">
        <h1 className="text-2xl font-semibold tracking-tight text-balance">
          {title}
        </h1>
        {lead && <div className="mt-2 text-ink-2">{lead}</div>}
      </div>
      {actions && (
        <div className="flex flex-wrap items-start gap-3 lg:justify-end">
          {actions}
        </div>
      )}
    </header>
  );
}
