---
name: document-verification
description: Build features that read documents (PDF, scans, DOCX, spreadsheets), extract facts with citations, cross-check documents against each other and against rules, and show findings a person can verify. Use for procurement files, investment-project documentation, contracts, invoices, budgets, certificates; for OCR choices; for Romanian identifiers (CUI/CIF, IBAN, CNP), amounts, dates and diacritics; and for RAG with pgvector.
---

# Document verification

The product's value is trust: a reviewer must be able to confirm every finding in seconds. Build
every feature around that.

## The pipeline

1. **Ingest.** Store the file once, keyed by its SHA-256 (re-uploads reuse earlier results). Keep
   the original; never overwrite it.
2. **Text per page.** Extract text page by page and keep the page number on everything downstream.
   Text PDFs: `pypdf` (BSD) or `pdfplumber` (MIT). Scans: see OCR below. A page whose text layer is
   nearly empty but holds an image is a scan.
3. **Extract.** One model call per page or small page group returns typed facts (amounts, dates,
   parties, identifiers, line items) through `AIClient.complete(schema=...)`. Every fact carries
   `page` and an exact `quote` from that page.
4. **Verify quotes.** Accept a fact only if its quote appears in the page text after normalisation
   (`quote_in_page` in [references/romanian-data.md](references/romanian-data.md)). A quote that
   is not on the page is a hallucination: drop the fact or flag it, never show it as evidence.
5. **Check in code.** Normalise values (amounts to `Decimal`, dates to `date`, identifiers
   validated), then run deterministic rules: sums, VAT, date order, the same party and identifier
   across documents, required documents present. The model never does arithmetic.
6. **Judge only what code cannot.** Use the model for semantic questions ("does this clause cover
   the guarantee required in the specification?"), again with quotes, and label the result as an
   AI judgement.
7. **Findings.** Each finding has a rule id, severity (`blocker`, `warning`, `info`), a sentence a
   reviewer understands, and evidence: one or more (document, page, quote, value). People confirm
   or dismiss findings; store their decision.

## Schemas that work on every provider

- Plain Pydantic models: required fields, `str | None` for optional values, no `Field(pattern=...,
  ge=..., min_length=...)`. Azure strict mode rejects those keywords; validate after parsing.
- Ask for values as text exactly as written (`"1.234.567,89"`), then parse in code. Models
  silently "fix" numbers when asked for floats.
- Keep one schema per document type and version prompts (`PROMPT_VERSION = "invoice-v3"`) so
  cached results can be invalidated.

```python
class Amount(BaseModel):
    label: str    # "Valoare totală fără TVA"
    value: str    # exactly as written on the page
    currency: str | None
    page: int
    quote: str    # the sentence or table row containing the value


class InvoiceFacts(BaseModel):
    supplier_name: str | None
    supplier_cui: str | None
    invoice_number: str | None
    issue_date: str | None
    amounts: list[Amount]
```

## Checks worth building first

Confirm the exact rules with the challenge brief and mentors; these are the usual sources of
mismatches ("necorelări") that cost money at settlement:

- Parties: the same name, CUI and address on the offer, contract, invoices and guarantees; CUI and
  IBAN check digits valid.
- Money: line quantity × unit price = line total; lines sum to the total; VAT applied at the rate
  valid on the document date; invoiced total ≤ contract value; budget line ≥ spent amount.
- Dates: offer ≤ contract signature ≤ start of works ≤ invoices ≤ end of contract; guarantee
  valid until the end of execution; documents dated before deadlines.
- Completeness: every document the procedure requires is present and signed.
- Consistency of descriptions: the item invoiced matches the item contracted (model judgement, with
  quotes from both documents).

Romanian VAT is time-dependent: 19% standard until 31 July 2025, 21% from 1 August 2025 (reduced
rates unified at 11%). Keep rates as dated data, never as a constant.

## OCR for scanned documents

| Option | Cost | Notes |
|---|---|---|
| Azure AI Document Intelligence `prebuilt-read` | $1.50 per 1,000 pages (S0) | Strong on Romanian scans; `prebuilt-layout` adds tables and costs more (check the pricing page) |
| Document Intelligence free tier (F0) | 500 pages per month | Analyses only the first 2 pages of each request, max 4 MB: send 2-page slices |
| Vision model on page images (render with `pypdfium2`) | Model token price per image | One call does OCR and extraction, but quotes must still be verified against what you show the user |

Keep OCR output per page with confidence where available, and show the page image next to the
finding for scans.

## Personal data

CNPs, private persons' IBANs, ID card numbers and addresses are personal data (GDPR). Mask them
before text reaches a model unless the check needs the value, keep documents in an EU region, and
never put real personal data in test fixtures or the demo.

## Retrieval (RAG)

Only when documents exceed the context window or the question spans many documents. Chunk per
page (or per section with the page kept), embed with `AIClient.embed`, store in pgvector, and
search by cosine distance. Tested model, index and query:
[references/pgvector.md](references/pgvector.md).

## Prove it works

- Keep a golden set: 3–10 real documents with the findings a human expects, in
  `api/tests/fixtures/` (public or synthetic documents only).
- Unit-test every deterministic rule and parser, including Romanian formats.
- Before a demo, run the golden set and note precision (false alarms erode trust faster than
  misses) and the cost per document from `ai_calls`.

## Cost and speed

- Cache extraction results by (file SHA-256, page, prompt version, model).
- Process pages concurrently with a small limit (`asyncio.Semaphore(4)`); one slow page must not
  block the others.
- Start with the cheapest model that passes the golden set; switch per task, not globally.
