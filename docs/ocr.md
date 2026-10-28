# OCR for scanned pages

Many funding documents are scans: their PDF pages are pictures with no text layer. The API reads
those pages with OCR, so they are checked, quoted and highlighted like any other page.

## How it works

1. **Upload.** `pdfplumber` reads the text layer. A page without one is stored empty and marked
   `ocr_status = pending` (`api/app/documents/ingest.py`). The upload answers at once.
2. **Background reading.** `api/app/documents/ocr_jobs.py` renders each pending page with PDFium
   (`pypdfium2`, at `OCR_DPI`) and hands the image to the OCR engine, `OCR_CONCURRENCY` pages at a
   time. Each page is saved as soon as it is read:
   - its text and word boxes, in PDF points like the text layer's;
   - each word's confidence and the page's mean confidence;
   - its CNPs, hashed and masked as on every page.
3. **Progress.** The workspace shows "Reading scanned pages: 3 of 12" and refreshes until the job
   is done. A check cannot start while pages are still being read (409).
4. **Stalls and failures.** OCR runs in the API process, so a restart or a scale-to-zero loses the
   job. A document whose pages stay unread for 15 minutes counts as stalled. Then **Read again**
   (`POST /api/projects/{id}/documents/{doc}/read-scans`) reads stalled or failed pages once
   more. Regulation PDFs have the same endpoint under `/api/regulation-documents/{id}/read-scans`.
5. **Checking.** OCR text goes through the same pipeline as a text layer: masking, extraction,
   quote verification and code checks. A page OCR could not read gets an "unreadable page"
   finding, so nobody assumes it was checked.

## How sure the reading was

OCR can misread a digit, and a misread CUI would become a false "invalid CUI" error. So a finding
whose evidence was read by OCR is at most as certain as its least certain highlighted word. When
the quote cannot be located, the page's mean confidence is used instead
(`api/app/verification/orchestrator.py`).

As a result, findings on shaky readings fall below the client's threshold
(`CLIENT_CONFIDENCE_THRESHOLD`, 0.85) but still reach reviewers (0.55). Every such finding is
labelled **Read by OCR** in the workspace.

## Settings

| Variable | Default | Meaning |
|---|---|---|
| `OCR_ENGINE` | `tesseract` | `none` switches OCR off; scanned pages are then flagged as unchecked |
| `OCR_LANGUAGES` | `ron+eng` | Tesseract language packs, best first |
| `OCR_DPI` | `300` | Render resolution; lower is faster but misses small print |
| `OCR_CONCURRENCY` | `2` (`1` on Azure) | Pages read at once; Tesseract uses a CPU core per page |
| `OCR_TIMEOUT_SECONDS` | `120` | Longest a single page may take |

The API image installs `tesseract-ocr` and `tesseract-ocr-ron` (`api/Dockerfile`); English comes
with them. `/status` shows the OCR row: the engine version and the installed languages, or what to
fix.

## Adding an engine

An engine implements `OcrEngine` (`api/app/ocr/base.py`):
- `recognize(png, dpi)` returns the words in image pixels with a confidence from 0 to 1;
- `probe()` reports whether the engine is ready.

Register it in `OCR_ENGINES` (`api/app/ocr/registry.py`) and add its name to `ocr_engine` in
`api/app/config.py`. Rendering, coordinate conversion, storage and confidence capping stay as they
are. Azure AI Document Intelligence (`prebuilt-read`) is the natural next engine for poor scans:
its words come with polygons and confidences.

## Known limits

- **Cropped or rotated pages.** pdfplumber measures boxes from the page's MediaBox, while PDF.js
  and PDFium use the CropBox and apply `/Rotate`. On such pages highlights can be offset.
- **Tables.** Tesseract reads tables line by line. Amounts are still found by their labels, but
  column structure is lost.
- **Speed.** At 300 dpi expect roughly 1 to 3 seconds per page per CPU core, so a 100-page scan
  takes minutes. The workspace shows the progress meanwhile.
