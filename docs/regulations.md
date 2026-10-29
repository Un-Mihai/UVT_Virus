# Regulation PDFs and retrieval

Requirements come from regulation PDFs and admin requirements written in natural language.
There is no automatically active catalogue of compliance rules. Python checks are tools the
model may request on behalf of an applicable requirement. The one exception is the small set of
form checks below, which need no regulation.

An admin selects a level in the regulation editor: all projects, a project type, or one project.
Each level has separate client and reviewer scopes. A verification combines the global PDFs,
its type's PDFs and its project's PDFs within the caller's scope. Written requirements apply
globally or to a type; requirements unique to a project come from that project's PDFs.

Uploading a PDF stores the original in PostgreSQL and schedules background processing:

1. Extract text per page, and OCR scanned pages when the configured OCR engine is available.
2. Mask personal identifiers and split text into passages, preserving PDF and page numbers.
3. Embed passages in batches through `AIClient.embed` and store the vectors and embedding model
   in `regulation_passages` (pgvector).

During verification, each user document is reviewed whole when it fits the context, so a period
or header stated on one page is not reported missing from another. A longer document is split
into consecutive excerpts that each repeat the start of the document, so the issuer stays known.
Each page becomes an embedding query; cosine-distance search retrieves only the regulation
passages applicable to that project and scope. The LLM compares those passages and written
requirements with the document, returning discrepancies and requests for Python checks. For
each discrepancy it first states whom the passage is addressed to and whether this document
falls under it; items it marks as not applying are dropped, which keeps another institution's
rules, data-category lists and other forms' instructions from becoming findings. It also quotes
the words that impose the obligation and says whether the passage is mandatory: a passage that
only allows (data an institution may process, collect or request) and the fill-in text of a
model form (dots, brackets, sample values) are permissions and templates, so those items are
dropped too. Code enforces it: the words must be in the passage verbatim and contain a word that
obliges ("trebuie", "obligatoriu", "se completează", "must"...; the list is in `compliance.py`).
A written rule is the admin's own wording and is not checked. Text set at a
diagonal angle (a SPECIMEN watermark) is left out of the extracted page text, and personal
identifiers reach the model as placeholders like `[CNP#1a2b3c]` that it must treat as present
values. A separate application review checks missing documents and form requirements. Evidence quotes
are validated against the user document and regulation passage before PDF-based semantic
findings are accepted. The panel shows findings, highlights and links to regulation pages.

The admin PDF list shows indexing and OCR status. If embeddings fail, extracted passages remain
available as a bounded text fallback starting at the beginning of the regulations. This fallback
can omit later requirements. Use **Process again** after fixing provider access or changing the
embedding model or dimensions. Search excludes incompatible vectors. Providers without an
embeddings endpoint need an embeddings-capable fallback; see [AI providers](ai-providers.md).

## Form checks

The forms agent (`api/app/verification/agents/form_checks.py`) runs in the first stage of every
verification, next to fact extraction, and calls no model. It scans every page of every document
and reports, as certain findings of severity bad, with the quote and its page:

- `forms.conflicting_marks`: two neighbouring options both ticked (`☒ necăsătorit(ă) ☒
  căsătorit(ă)`). Only neighbours count: one line may hold several independent questions.
- `forms.consent_refused`: `☐ DA ☒ NU sunt de acord`. Other DA/NU questions (PEP, FATCA, marketing)
  are not consents the file depends on.
- `forms.consent_incomplete`: on a consent form ("ACORD DE CONSULTARE"), a list of items where
  some carry an "X" and others do not (F5 with `d)` left out).
- `forms.certificate_expired`: a certificate that says "valabilă N zile de la data emiterii" and
  was issued more than N days before the date of the credit application ("din data de ...").
- `forms.id_expired`: the identity card's "Valabil până la" (in the application and in the KYC
  form, reported once) is before the date of the credit application.
- `forms.installment_undeclared`: a statement shows "Plată rată" lines to the same payee in at
  least two months, and their monthly sum is more than the application's "Total rate lunare
  existente declarate".
- `forms.income_below_declared`: the ANAF income certificate has one row for the year so far.
  Its taxable income less tax, over the months before the last D112 it cites (from the hiring
  month when the job began that year), is under 80% of the application's "Venit net mediu -
  ultimele 6 luni".

The CNP check digit (`personal_data.cnp_valid`) runs there too, on every verification, whether or
not the model asks for it; when it does, the orchestrator keeps one finding, the one that cites
a regulation.

A group of options that wraps onto the next line is compared line by line. Add a check by writing
its pattern in that module, its sentences in `messages.py` (English and Romanian) and a test.

## Documents to add

Each project has a list of documents its applicant must add (`required_documents`, shown on the
project page with an upload button per item, and ticked once a PDF was uploaded for it; the
owner can also pick the item an already uploaded document is for, in the document list). By
default it is read from the **client-scope** regulations that apply to the project (every
project, its type, the project itself) and the admins' written rules: a background job right
after the project is created, or an admin's **Read from the regulations** button on the project's
level in the regulation editor. Retrieval asks for the documents an applicant must submit, in
Romanian and English, for this project type. For each passage the model first states whom it
asks for a document and whether it applies (items marked as not applying are dropped), then
names the document with the exact quote; an item whose quote is not in its passage, whose source
was not given, or whose name repeats an earlier one is dropped in code. Items keep the regulation
and page they were read from.

An admin can add, edit and delete items for a project. An edited item becomes the admin's and is
kept when the regulations are read again; items still read from the regulations are replaced by
the new reading. Reading is not repeated by itself when regulations change later: use the button.
Without a provider or applicable regulations the list stays empty. It is guidance for the
applicant: submitting does not depend on it. Verification does: it first checks that every item
has a document uploaded for it (a document uploaded outside the list does not count). When one
has none, the run reports one finding per missing item and stops: no page is read, no regulation
is retrieved and no model is called until the file is complete.

Apply migrations with `docker compose exec api alembic upgrade head`. Existing PDFs uploaded
before passage indexing was introduced need **Process again**. Background processing runs in
the API process; after a restart, retry interrupted uploads. Vector search is exact, with no
approximate index, appropriate for the current regulation collection.
