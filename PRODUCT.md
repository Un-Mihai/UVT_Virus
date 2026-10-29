# Product

<!-- impeccable:product-schema 1 -->

Fill in the open decisions as soon as the team settles them; every agent reads this file.

## Platform

web

## Users

Open decision: the challenge track is confirmed on 27 October 2026. The working assumption is
staff who check large sets of documents by hand, such as bank teams reviewing documentation for
investment projects or procurement files before money is released.

Everyone signs in (docs/auth.md). The realm (`infra/keycloak/realm-app.json`) has three roles,
enforced in the API with `require_roles`:

- `client`: applies for funding projects. Fills in the form, uploads documents (stored in
  PostgreSQL) and starts the **Client Verification Process**, which checks the file against the
  client eligibility rules with a high confidence threshold (`CLIENT_CONFIDENCE_THRESHOLD`,
  e.g. `0.85`). The client gets a high-certainty summary and the highlighted document, with the
  exact quote, the reason for each error and a recommended change.
- `reviewer`: inspects and verifies the projects clients submit, through a separate **Reviewer
  Verification Process**. It checks against the internal audit and compliance rules with a lower
  threshold (`REVIEWER_CONFIDENCE_THRESHOLD`, e.g. `0.55`), so it shows definite errors and
  medium-confidence findings.
- `admin`: uploads, views and edits the active regulation documents and rule sets per funding
  project type, kept apart for the client scope and the reviewer scope.

## Product Purpose

Help people verify documents for public procurement and investment projects faster. The product
reads the documents in a file, finds inconsistencies between them (amounts, dates, parties,
identifiers, required documents) and shows each finding with the page and quote it comes from, so
a person can confirm or dismiss it. Errors caught before submission avoid funds being cut at
settlement because documents do not match.

Success: a reviewer reaches the same conclusions in a fraction of the time, and every flagged
inconsistency can be traced to its source in one click.

## Positioning

Open decision. Candidate: evidence-first verification. Every finding carries its source quote and
page, and the checks that matter (sums, dates, identifiers) are computed in code, not guessed.

## Operating Context

- Documents are mostly Romanian PDFs: many are scans, many are long, tables carry the amounts.
- Hackathon: NEXXT AI Hackathon, Bucharest, 28–29 October 2026, track "Raiffeisen Bank —
  Operational Efficiency: AI agents that reduce repetitive work involving documents, data and
  verification". Submission and video pitch are due on the second morning.
- AI runs on whatever endpoint `.env` names (organiser tokens, Azure for Students credits via
  Azure AI Foundry, or another OpenAI-compatible provider), so the client can bring their own.

## Capabilities and Constraints

- Decided: requirements come only from uploaded regulation PDFs or admin requirements written in
  natural language. The LLM derives applicable requirements dynamically during verification;
  executable checks are tools it may request when a supplied requirement needs calculation.
- Decided: one exception to the line above, the forms agent
  (`api/app/verification/agents/form_checks.py`): on every verification, in both scopes, it reads
  the boxes and dates of every page in code, with no model call and no regulation needed, and
  reports (certain, severity bad) two neighbouring options both ticked, a consent answered "NU"
  (`☐ DA ☒ NU sunt de acord`), a consent list ticked in part (F5 with a letter left out), and an
  income certificate older than the validity it states for itself (compared with the date of the
  credit application), an identity card whose "Valabil până la" is before that date, and monthly
  loan instalments paid in a statement that the application's "Total rate lunare existente
  declarate" does not cover, and an ANAF certificate whose monthly net income is under 80% of the
  net average the application declares. The CNP check digit runs every time too. A model skims
  these; code does not.
- Decided: a regulation passage that only allows something (data an institution may process,
  collect or request) or is the fill-in text of a model form is not a requirement. The model must
  quote the passage's own words that oblige; code drops the finding when they are not verbatim or
  contain no word of obligation.
- Decided: a regulation passage from one bank's own documents (its general conditions, product
  page, information note) is not applied to a document issued by another institution; the
  compliance prompt says so. Removing such PDFs from the admin list is the hard way to the same.
- Decided: regulation PDFs may apply globally, to a project type, or to one project. A project
  inherits all three levels within its verification scope (`client` or `reviewer`). Project-only
  requirements come from its PDFs; admin-written requirements apply globally or to a type.
- Database persistence (PostgreSQL with pgvector): original regulation PDFs, page-numbered text
  passages and their embeddings, the client's form input (JSON), uploaded files (raw bytes and
  extracted pages), and verification findings (`DocumentFinding`).
- Regulation ingestion extracts text, runs OCR for scans, splits each page into passages, and
  embeds them through `AIClient`. Verification retrieves applicable passages by cosine distance
  and compares every user document page with those passages and admin-written requirements.
  Findings appear in the verification panel with document highlights and regulation citations.
  Sums, dates and identifiers are checked in Python.
- Decided: indexing failures retain extracted passages for bounded text fallback and allow an
  admin to process the PDF again. Changing the embedding model or dimensions requires reindexing
  for vector retrieval; incompatible vectors are excluded from similarity search.
- The backend returns the annotated, highlighted document and highlight anchors together with the
  error reasons and change recommendations.
- Proposed (confirm): the cost per checked document is measured and shown, from the `ai_calls`
  ledger.
- Decided: CNPs are masked before any text reaches a model (a stable placeholder per person). They
  are compared across the documents and the form only as keyed hashes (HMAC,
  `PERSONAL_DATA_HASH_KEY`), and stored and shown only masked. Private persons' IBANs are not
  masked yet.
- Decided: people confirm or dismiss each finding, and the decision is stored with who made it and
  when. Clients decide on client-scope findings, reviewers on reviewer-scope findings.
- Decided: the document viewer renders the original PDF; the backend returns highlight boxes per
  finding (`/highlights`) and an annotated PDF (`/annotated`), both keyed by `finding-{id}`.
- Decided: a reviewer's home lists every applicant who submitted (organisation from the form,
  account name, project, submitted date, state) and picks one by opening their file. A client's
  file state is derived: draft, waiting for a reviewer, or in review (a reviewer has started the
  Reviewer Verification Process, counted from the latest submission); each document also shows its
  own check state.
- Decided: a reviewer records a verdict on a submitted file (`PUT /api/projects/{id}/verdict`).
  Approved keeps it submitted and locked. Changes requested needs a note and sends the file back
  to its owner as a draft, so it leaves the reviewer's list; submitting again clears the verdict.
  The client sees the verdict and the note on their file. Reviewers never see a returned file
  until it is resubmitted.
- Decided: each project has a list of documents to add, shown to its applicant (and to the
  reviewer) with what was uploaded for each item (`GET /api/projects/{id}/required-documents`; an
  upload names its item with `required_document_id`, and the owner can tie a document
  already uploaded to an item, or untie it, with `PATCH /api/projects/{id}/documents/{doc}`). By default it is read from the client-scope
  regulations that apply to the project, each item with the regulation and page that require it
  (a background job when the project is created, or an admin reading again); an admin can add,
  edit and delete items, and an edited item survives a new reading. The list does not block
  submitting, but a verification of a project with an item that has no document reports only
  that (one finding per missing item, in both scopes) and checks no document.
- Open decision: which document types and which checks the demo covers. The deterministic checks
  available to rule sets are listed at `GET /api/checks`.
- Open decision: whether reviewers can correct an extracted value and re-run the checks.
- Decided: scanned pages are read by OCR (Tesseract with the Romanian pack, in the API image)
  right after upload, and checked like text pages (docs/ocr.md). Pages OCR cannot read are
  flagged as unchecked.
- Decided: a finding whose evidence was read by OCR is at most as certain as its least certain
  highlighted word, and is labelled "Read by OCR". Shaky readings reach reviewers but not clients.

## Evidence on Hand

None yet. Use real public procurement documents (published on SEAP/SICAP) or documents the
challenge partner provides. Never invent documents, findings, customers or metrics; label any
synthetic demo data as synthetic.

## Product Principles

Proposed; confirm or rewrite as a team.

1. Every finding shows its evidence: document, page, exact quote.
2. People decide; the product never approves or rejects on its own.
3. Code computes, the model reads: arithmetic and comparisons are deterministic.
4. Cost and speed per document are visible, not promised.

## Accessibility & Inclusion

Decided: the interface is in English and Romanian, switchable on every page; the language is
part of the address (`/en/...`, `/ro/...`) and remembered. Findings carry their reason and
recommendation in both languages. Quotes stay in the documents' own language.

Proposed baseline: WCAG 2.2 AA contrast, every status conveyed by text and not colour alone, a
review flow that works with the keyboard only.
