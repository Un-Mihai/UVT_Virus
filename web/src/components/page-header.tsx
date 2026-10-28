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
    <header className="page-header grid gap-6 border-b border-line pb-8 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-center lg:gap-x-12">
      <div className="max-w-prose min-w-0">
        <h1 className="text-3xl leading-tight font-bold tracking-tight text-balance sm:text-4xl">
          {title}
        </h1>
        {lead && (
          <div className="mt-3 text-base/relaxed text-ink-2">{lead}</div>
        )}
      </div>
      {actions && (
        <div className="flex flex-wrap items-start gap-3 lg:justify-end">
          {actions}
        </div>
      )}
    </header>
  );
}
