"use client";

import type {
  PDFDocumentLoadingTask,
  PDFDocumentProxy,
  RenderTask,
} from "pdfjs-dist";
import { type ReactNode, useEffect, useRef, useState } from "react";

import { fill } from "@/i18n/template";
import { type PageBox, rectStyle } from "@/lib/pdf/geometry";
import { openPdf } from "@/lib/pdf/load";

export type ViewerPage = PageBox & { number: number };

export type ViewerHighlight = {
  id: number;
  page: number;
  rects: number[][];
  severity: "bad" | "warn";
  /** Accessible name of the highlight, e.g. "Error: the CUI fails its check digit". */
  label: string;
  /** Shown next to the passage while the highlight is active. */
  note: ReactNode;
};

/** Ask the viewer to scroll to a highlight and focus it; a new object each time. */
export type JumpRequest = { id: number } | null;

type Text = { loading: string; failed: string; page: string };

const tint = {
  bad: "bg-bad/25 hover:bg-bad/40",
  warn: "bg-warn/30 hover:bg-warn/45",
} as const;

/** The original PDF, page by page, with the findings drawn over it (DESIGN.md: review workspace). */
export function DocumentViewer({
  url,
  pages,
  highlights,
  activeId,
  jump,
  onSelect,
  text,
}: {
  url: string;
  pages: ViewerPage[];
  highlights: ViewerHighlight[];
  activeId: number | null;
  jump: JumpRequest;
  onSelect: (id: number) => void;
  text: Text;
}) {
  const [loaded, setLoaded] = useState<{
    url: string;
    pdf: PDFDocumentProxy | null;
  } | null>(null);

  useEffect(() => {
    let cancelled = false;
    let task: PDFDocumentLoadingTask | undefined;
    openPdf(url)
      .then((loading) => {
        task = loading;
        if (cancelled) return loading.destroy();
        return loading.promise.then((pdf) => {
          if (!cancelled) setLoaded({ url, pdf });
        });
      })
      .catch(() => {
        if (!cancelled) setLoaded({ url, pdf: null });
      });
    return () => {
      cancelled = true;
      void task?.destroy();
    };
  }, [url]);

  useEffect(() => {
    if (!jump) return;
    const target = document.getElementById(`finding-${jump.id}`);
    if (!target) return;
    const still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    target.scrollIntoView({
      behavior: still ? "auto" : "smooth",
      block: "center",
    });
    target.focus({ preventScroll: true });
  }, [jump]);

  const pdf = loaded?.url === url ? loaded.pdf : undefined;
  return (
    <div className="flex flex-col gap-4">
      {pdf === null && (
        <p role="alert" className="text-bad">
          {text.failed}
        </p>
      )}
      {pdf === undefined && (
        <p aria-live="polite" className="text-sm text-ink-3">
          {text.loading}
        </p>
      )}
      {pages.map((page) => (
        <ViewerPageBox
          key={page.number}
          pdf={pdf ?? null}
          page={page}
          label={fill(text.page, { page: page.number })}
        >
          {highlights
            .filter((highlight) => highlight.page === page.number)
            .map((highlight) => (
              <Highlight
                key={highlight.id}
                highlight={highlight}
                page={page}
                active={highlight.id === activeId}
                onSelect={onSelect}
              />
            ))}
        </ViewerPageBox>
      ))}
    </div>
  );
}

/** One page: a box with the page's proportions at once, its canvas drawn when it nears view. */
function ViewerPageBox({
  pdf,
  page,
  label,
  children,
}: {
  pdf: PDFDocumentProxy | null;
  page: ViewerPage;
  label: string;
  children: ReactNode;
}) {
  const box = useRef<HTMLDivElement>(null);
  const canvas = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const element = box.current;
    if (!pdf || !element) return;
    let cancelled = false;
    let task: RenderTask | undefined;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry?.isIntersecting) return;
        observer.disconnect();
        void pdf.getPage(page.number).then((pdfPage) => {
          const target = canvas.current;
          if (cancelled || !target) return;
          // Sharp on high-density screens, capped so long documents stay light on memory.
          const pixels = Math.min(
            element.clientWidth * window.devicePixelRatio,
            2400,
          );
          const viewport = pdfPage.getViewport({
            scale: pixels / pdfPage.getViewport({ scale: 1 }).width,
          });
          target.width = Math.floor(viewport.width);
          target.height = Math.floor(viewport.height);
          task = pdfPage.render({ canvas: target, viewport });
          task.promise.catch(() => {}); // cancelled renders reject; nothing to show for them
        });
      },
      { rootMargin: "800px 0px" },
    );
    observer.observe(element);
    return () => {
      cancelled = true;
      observer.disconnect();
      task?.cancel();
    };
  }, [pdf, page.number]);

  return (
    <div
      ref={box}
      role="group"
      aria-label={label}
      className="relative w-full overflow-hidden rounded-md border border-line bg-surface-2"
      style={{ aspectRatio: `${page.width} / ${page.height}` }}
    >
      <canvas ref={canvas} aria-hidden className="absolute inset-0 size-full" />
      {children}
    </div>
  );
}

function Highlight({
  highlight,
  page,
  active,
  onSelect,
}: {
  highlight: ViewerHighlight;
  page: ViewerPage;
  active: boolean;
  onSelect: (id: number) => void;
}) {
  const [first, ...rest] = highlight.rects;
  if (!first) return null;
  const last = highlight.rects.at(-1) ?? first;
  const ring = active
    ? highlight.severity === "bad"
      ? "outline-2 outline-bad"
      : "outline-2 outline-warn"
    : "";
  const below = (last[3] ?? 0) / page.height < 0.75;
  return (
    <>
      <button
        type="button"
        id={`finding-${highlight.id}`}
        aria-label={highlight.label}
        aria-pressed={active}
        onClick={() => onSelect(highlight.id)}
        className={`absolute transition-colors duration-150 ${tint[highlight.severity]} ${ring}`}
        style={rectStyle(first, page)}
      />
      {rest.map((rect, index) => (
        <span
          key={index}
          aria-hidden
          onClick={() => onSelect(highlight.id)}
          className={`absolute cursor-pointer transition-colors duration-150 ${tint[highlight.severity]} ${ring}`}
          style={rectStyle(rect, page)}
        />
      ))}
      {active && (
        <div
          className="absolute inset-x-3 z-10 rounded-md border border-line-strong bg-surface p-3 text-sm text-ink"
          style={
            below
              ? {
                  top: `calc(${rectStyle(last, page).top} + ${rectStyle(last, page).height} + 0.5rem)`,
                }
              : {
                  bottom: `calc(100% - ${rectStyle(first, page).top} + 0.5rem)`,
                }
          }
        >
          {highlight.note}
        </div>
      )}
    </>
  );
}
