// The PDF.js worker. load.ts starts it with new Worker(new URL(...)) so Turbopack bundles it;
// the module wires itself to the worker scope when it loads.
import "pdfjs-dist/build/pdf.worker.min.mjs";
