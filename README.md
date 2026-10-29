# UVT Virus: document checks for credit files

Built for the NEXXT AI Hackathon (Bucharest, 28–29 October 2026), track "Raiffeisen Bank:
Operational Efficiency". An applicant uploads the documents of a consumer-credit file, the app
reads them (scans included), compares them with the applicable regulations and with each other, and
shows every finding next to the highlighted page it comes from, with the exact quote, the reason
and a recommended change. People decide; the product never approves or rejects on its own.

The app is called **Document checks** on screen, in English and Romanian. Product decisions live
in [PRODUCT.md](PRODUCT.md), the design system in [DESIGN.md](DESIGN.md).

## Who uses it

Everyone signs in with Keycloak. Roles are enforced in the API, not only by hiding buttons.

| Role | Does | Sees |
|---|---|---|
| `client` | Creates an application, fills in the form, uploads documents, submits, runs the **Client Verification Process** | Client-scope findings with confidence ≥ 0.85, and the reviewer's verdict on the file |
| `reviewer` | Opens submitted files, runs the **Reviewer Verification Process**, confirms or dismisses each finding, approves the file or sends it back with a note | Reviewer-scope findings with confidence ≥ 0.55 |
| `admin` | Manages project types, regulation PDFs, written requirements and each project's list of documents to add | Both scopes of the regulation editor |

The thresholds are `CLIENT_CONFIDENCE_THRESHOLD` and `REVIEWER_CONFIDENCE_THRESHOLD`. The two
scopes never share rules. Details: [docs/auth.md](docs/auth.md).

## How a verification works

1. **Completeness gate.** Each project has a list of documents to add, read from the client-scope
   regulations (or written by an admin). If an item has no upload, the run reports one finding per
   missing item and stops: no page is read and no model is called until the file is complete.
2. **Facts and forms, in parallel.** The extraction agent reads facts from each document. The forms
   agent works in code, with no model: two neighbouring options both ticked, a refused or partly
   ticked consent, an expired income certificate or identity card, loan instalments the application
   does not declare, income under 80% of the declared average, and the CNP check digit.
3. **Compliance.** Each page becomes a query against the regulation passages stored in pgvector
   (global, project-type and project-specific PDFs, plus written requirements). The model states
   whom a passage addresses and quotes the words that oblige; code drops findings whose quote is
   not verbatim or carries no word of obligation.
4. **Code checks the model may request.** Totals, dates, CNP, CUI and IBAN validity and
   cross-document comparisons are computed in Python (`GET /api/checks` lists them).
5. **Findings.** Each one carries severity, confidence, source document and page, the quote, the
   regulation and page it cites, and its reason and recommendation in both languages. The viewer
   renders the original PDF with highlight boxes, and an annotated PDF can be downloaded.

Personal identifiers are masked before text reaches a model (CNP becomes a placeholder) and are
compared across documents only as keyed hashes. A finding read from a scan is at most as certain as
its least certain word and is labelled "Read by OCR". Regulation retrieval:
[docs/regulations.md](docs/regulations.md). OCR: [docs/ocr.md](docs/ocr.md).

## What is implemented

- **Applications.** Form, document upload (stored in PostgreSQL), edit, submit; file states draft,
  waiting for a reviewer, in review; verdict "approved" or "changes requested" with a note.
- **Reviewer inbox.** Submitted files with applicant, project, date and state; a review pane with
  the findings list beside the document, and a stored confirm or dismiss decision per finding.
- **Regulation editor.** Project types, regulation PDFs at three levels (all projects, a type, one
  project) and two scopes, indexing and OCR status per PDF with **Process again**, written
  requirements, and each project's documents to add.
- **OCR.** Pages without a text layer are read in the background with Tesseract (Romanian and
  English), then checked and highlighted like text pages.
- **AI.** Any OpenAI-compatible endpoint chosen only in `.env`; every call goes through `AIClient`,
  which enforces a daily budget, fails over to a second account and records tokens and cost in
  `ai_calls`. Providers: [docs/ai-providers.md](docs/ai-providers.md).
- **Status page.** `/status` shows web, API, database, sign-in, OCR and AI, and runs a live AI check.
- **Azure.** Terraform for Container Apps, PostgreSQL, Container Registry, AI Foundry and
  Keycloak: [docs/deploy-azure.md](docs/deploy-azure.md).

## Stack

| Layer | Technology |
|---|---|
| Web | Next.js 16.4 (App Router, React 19.3, React Compiler, Cache Components), TypeScript, Tailwind CSS 4, pdf.js |
| API | FastAPI, Python 3.13, Poetry, SQLAlchemy 2 (async), Alembic |
| Data | PostgreSQL 17 with pgvector (exact cosine search) |
| Sign-in | Keycloak 26 (OpenID Connect with PKCE); tokens stay in encrypted httpOnly cookies on the server |
| AI | `AI_PROVIDER=openai`, `azure` or `bedrock`; default models `gpt-5-mini` and `text-embedding-3-small` |
| OCR | Tesseract with the Romanian pack, in the API image |
| Local | Docker Compose |
| Cloud | Terraform on Azure |
| Quality | Ruff, mypy, pytest, ESLint, Prettier, Vitest, knip, impeccable and taste UI linters, GitHub Actions |

The browser only talks to Next.js. Server Components call FastAPI directly; client code goes
through `/api/*`, which Next.js forwards with the user's access token. On Azure the API is not
public.

## Setup

### 1. Install these yourself

| Tool | Why | How |
|---|---|---|
| Git | Clone and commit | macOS: `xcode-select --install` · Ubuntu/WSL: `sudo apt install git` |
| Docker Desktop (Docker Engine on Linux) | Runs web, API, database and Keycloak | [docs.docker.com/get-docker](https://docs.docker.com/get-docker/) |
| WSL 2 with Ubuntu (Windows only) | Docker Desktop and the setup script run there | `wsl --install`, then clone inside WSL, not under `/mnt/c` |
| Homebrew (macOS only) | The setup script installs tools with it | [brew.sh](https://brew.sh) |

### 2. Create `.env`

`.env` is not committed. Create it in the repo root with the AI account you use:

```bash
AI_PROVIDER=azure
AZURE_AI_BASE_URL=https://<resource>.openai.azure.com/openai/v1/
AZURE_AI_API_KEY=<key>
```

[docs/ai-providers.md](docs/ai-providers.md) has ready-made blocks for Azure AI Foundry, AWS
Bedrock, OpenAI, local models and a fallback account. Every other setting has a default in
`api/app/config.py`. Without an AI account the app starts, but verification and regulation
indexing need one.

### 3. Run the setup

```bash
git clone https://github.com/Un-Mihai/UVT_Virus.git
cd UVT_Virus
make setup
```

Without `make`, run `bash scripts/setup.sh`. The script installs any missing tool below without an
admin password, installs the web and API dependencies, and starts the stack on
http://localhost:3000. `make doctor` reports what is installed without changing anything.

| Installed for you | Used for | To install it yourself instead |
|---|---|---|
| Node.js 22+ | Editor types, Next.js docs for agents, `make check-ui`, MCP servers | `brew install node` · [nodejs.org](https://nodejs.org/en/download) |
| Terraform 1.9+ | Azure deployment | `brew install hashicorp/tap/terraform` · [install guide](https://developer.hashicorp.com/terraform/install) |
| Azure CLI | Azure login and deployment | `brew install azure-cli` · Ubuntu/WSL: `curl -sL https://aka.ms/InstallAzureCLIDeb \| sudo bash` |
| Poetry 2 and Python 3.13 | Running the API outside Docker, editor support | `brew install poetry python@3.13` · [python-poetry.org](https://python-poetry.org/docs/#installation) |

On Linux and WSL the tools go into `~/.local/bin`; add it to your `PATH` if the setup says so.

### 4. Sign in and try it

Open http://localhost:3000 and sign in with password `demo` as:

- `client`: create an application and upload documents.
- `reviewer`: open the submitted file and run the review.
- `admin` (also a reviewer): create a project type and upload regulation PDFs.

Press **Run AI check** on http://localhost:3000/status to confirm the AI account works.

## Sample data

- `Date test/`: 22 applicant folders (`P_001`, `P005` … `P087`) of fictitious applicants, up to
  eight files each: credit application, ANAF consent, GDPR/FATCA/CRS/PEP declaration, income
  certificate, bank statement, credit bureau consent, CRC consent and an identity card image. Some
  folders are missing documents. The identity cards are stamped as test documents with fictitious
  data.
- `Reguli (2)/Reguli/`: the regulations for a new lei consumer loan to a salaried individual
  (Raiffeisen Flexicredit): BNR regulations, OUG 50/2010, Legea 129/2019, GDPR, Raiffeisen's public
  documents and more. Its own `README_reguli.md` says which PDFs to index; the subfolders hold HTML
  sources, repealed texts and full texts that are not indexed.

Upload the regulation PDFs in `/en/admin/regulations`, then the files of an applicant as `client`.

## Commands

| Command | What it does |
|---|---|
| `make setup` / `make doctor` | Install what is missing / only report |
| `make up` / `make down` | Start or stop the stack; run `make up` again after every pull |
| `make logs` | Follow API and web logs |
| `make reset-auth` | Re-import the users and roles from `infra/keycloak/realm-app.json` |
| `make reset-db` | Delete the local database (then `make up`) |
| `make check` | Every API and web check (`check-api`, `check-web`) |
| `make check-ui` | Impeccable on source and rendered pages, plus taste's linter |
| `make fix` | Formatting and autofixable lint |
| `make migration m="add documents"` | Alembic migration from `api/app/models.py` |
| `make gen-api` | Regenerate the web app's API types after an API change |
| `make criteria` | Re-read the hackathon's official rules, criteria and schedule and report changes |
| `make sync-agents` | Copy `.agents/skills` to the Claude Code and Kiro folders |
| `make deploy` | Build, push and deploy to Azure |
| `make help` | The same list from the Makefile |

CI (`.github/workflows/ci.yml`) runs the API and web checks, builds the production images and
checks the skills and scripts on every push to `main` and every pull request.

## Layout

```text
api/                 FastAPI
  app/ai/            AIClient (the only AI client) and providers
  app/routes/        projects, verifications, findings, regulations, project_types,
                     required_documents, ai, ocr_status, me, health
  app/verification/  orchestrator, agents (completeness, extraction, form checks, compliance),
                     code checks registry, findings, bilingual messages, scopes
  app/regulations/   PDF passages, chunking, levels, pgvector search
  app/documents/     uploads, page reading, OCR jobs
  app/ocr/, app/pdf/ OCR engines; PDF reading, locating quotes, annotating
  app/personal_data/ CNP detection, HMAC hashing, masking
  app/projects/      access rules, form schema, documents to add
  migrations/        Alembic (seven revisions so far)
  tests/             pytest against a real test database and a fake AI provider
web/                 Next.js
  src/app/[lang]/    pages in English and Romanian: home, projects (new, view, edit, review),
                     admin/regulations, status
  src/app/api/       proxy to the API
  src/app/auth/      sign-in, callback, sign-out; src/proxy.ts adds the language and session
  src/components/    shared UI pieces, including the PDF document viewer
  src/i18n/          English and Romanian dictionaries
  src/lib/           API clients, auth, pdf.js helpers
infra/keycloak/      Realm (users, roles, web client) and the Azure image
infra/terraform/     Azure infrastructure, with offline tests
Date test/           Sample applicant files
Reguli (2)/Reguli/   Regulations for the sample credit product
docs/                Sign-in, AI providers, regulations and retrieval, OCR, Azure, agents, judging
scripts/             setup.sh, deploy.sh, signed_in.mjs, sync_agents.py, judging_criteria.py
.agents/skills/      Agent skills; copies in .claude/ and .kiro/
AGENTS.md            Rules every AI coding agent reads
```

## Working with AI coding agents

Agents read [AGENTS.md](AGENTS.md) (Claude Code through `CLAUDE.md`); [docs/agents.md](docs/agents.md)
shows how each tool is wired. Skills live in `.agents/skills/`: `impeccable` and
`design-taste-frontend` for UI, `ponytail*` for small changes and reviews, `document-verification`
for extraction and checks, `azure-deploy`, `hackathon-judge` (scores the project against the
organisers' criteria, rubric in [docs/judging/rubric.md](docs/judging/rubric.md)) and
`hackathon-pitch`. Before you merge: `make check`, plus `make check-ui` and a look at a phone-sized
window for UI work.

## Troubleshooting

- **Port already in use:** set `WEB_PORT`, `API_PORT`, `DB_PORT` or `KEYCLOAK_PORT` in `.env`,
  then `make up`; after changing `WEB_PORT`, also `make reset-auth`.
- **Keycloak says "Invalid parameter: redirect_uri":** `make reset-auth`.
- **Pulled or added a dependency, or "Module not found":** `make up`. It rebuilds the images and
  gives the web container a fresh `node_modules`; the database is kept.
- **Fresh database:** `make reset-db`, then `make up`.
- **A verification stops with a list of missing documents:** upload a document for each item in
  the project's "documents to add" list; the run checks nothing else until it is complete.
- **A regulation PDF shows an indexing error:** fix the AI account in `.env`, restart the API
  (`docker compose up -d --force-recreate api`) and press **Process again** in the regulation editor.
- **A tool is "not found" after setup on Linux or WSL:** add `~/.local/bin` to your `PATH`.

Third-party skills and fonts keep their licences: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
