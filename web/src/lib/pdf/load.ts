import type { PDFDocumentLoadingTask } from "pdfjs-dist";

let worker: Worker | undefined;

/** Starts loading a PDF in the browser with PDF.js; destroy the task to release it. Call it
 *  from effects or handlers only: PDF.js needs the DOM at import time. */
export async function openPdf(url: string): Promise<PDFDocumentLoadingTask> {
  const pdfjs = await import("pdfjs-dist");
  // One worker for every document; Turbopack bundles it from this new Worker(new URL()) call.
  worker ??= new Worker(new URL("./pdf.worker.ts", import.meta.url), {
    type: "module",
  });
  pdfjs.GlobalWorkerOptions.workerPort = worker;
  return pdfjs.getDocument({ url });
}
