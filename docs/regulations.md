# Regulation PDFs and retrieval

Requirements come from regulation PDFs and admin requirements written in natural language.
There is no automatically active catalogue of compliance rules. Python checks are tools the
model may request on behalf of an applicable requirement.

An admin selects a level in the regulation editor: all projects, a project type, or one project.
Each level has separate client and reviewer scopes. A verification combines the global PDFs,
its type's PDFs and its project's PDFs within the caller's scope. Written requirements apply
globally or to a type; requirements unique to a project come from that project's PDFs.

Uploading a PDF stores the original in PostgreSQL and schedules background processing:

1. Extract text per page, and OCR scanned pages when the configured OCR engine is available.
2. Mask personal identifiers and split text into passages, preserving PDF and page numbers.
3. Embed passages in batches through `AIClient.embed` and store the vectors and embedding model
   in `regulation_passages` (pgvector).

During verification, each user document is reviewed in page excerpts, including later pages of
long documents. Excerpts become embedding queries; cosine-distance search retrieves only the
regulation passages applicable to that project and scope. The LLM compares those passages and
written requirements with the document, returning discrepancies and requests for Python checks.
A separate application review checks missing documents and form requirements. Evidence quotes
are validated against the user document and regulation passage before PDF-based semantic
findings are accepted. The panel shows findings, highlights and links to regulation pages.

The admin PDF list shows indexing and OCR status. If embeddings fail, extracted passages remain
available as a bounded text fallback starting at the beginning of the regulations. This fallback
can omit later requirements. Use **Process again** after fixing provider access or changing the
embedding model or dimensions. Search excludes incompatible vectors. Providers without an
embeddings endpoint need an embeddings-capable fallback; see [AI providers](ai-providers.md).

Apply migrations with `docker compose exec api alembic upgrade head`. Existing PDFs uploaded
before passage indexing was introduced need **Process again**. Background processing runs in
the API process; after a restart, retry interrupted uploads. Vector search is exact, with no
approximate index, appropriate for the current regulation collection.
