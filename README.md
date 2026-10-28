# AI engineering project template (Azure)

A full-stack starter built to be developed with AI coding agents: a Next.js web app, a FastAPI
service, PostgreSQL with pgvector, Keycloak sign-in and an AI client for any OpenAI-compatible
provider. It runs
locally in Docker and deploys to Azure with one command. Claude Code, Codex, Antigravity, Kiro,
Cursor, Copilot and other agents share the same rules, skills and quality gates, so what they
build stays consistent and free of "AI slop".

## What it gives you

- **A working stack on day one.** Web, API, database and AI are wired together; `/status` shows
  each one and runs a live AI check.
- **AI from environment variables only.** Azure AI Foundry, OpenAI, hackathon tokens or local
  models, switched in `.env`; `AI_PROVIDER=azure` uses the Azure backend API and
  `AI_PROVIDER=bedrock` uses an AWS Bedrock API key. A second account takes over when the first fails or runs out of
  credit, a daily budget caps spend, and every call is logged with its tokens and cost.
- **Sign-in from the start.** Keycloak (OpenID Connect) locally and on Azure: every page and API
  call needs a user, roles arrive in each token, and demo accounts are ready for the jury
  ([docs/auth.md](docs/auth.md)).
- **Three roles, two verification pipelines.** `client` applies for funding and gets a
  high-confidence check against the client rules; `reviewer` audits submissions against the
  internal rules at a lower threshold; `admin` manages the regulations for each. Each role sees
  only its own rule set's findings.
- **Everything is stored.** Regulations per project type and scope, client form input, and the
  uploaded and highlighted documents are persisted in PostgreSQL.
- **Highlights-only review.** A list of flagged findings beside the highlighted document; click a
  finding and the viewer jumps to its page and passage.
- **Scans are read.** Pages without a text layer are read with OCR (Tesseract, Romanian and
  English) in the background, then checked and highlighted like text pages
  ([docs/ocr.md](docs/ocr.md)).
- **English and Romanian.** Every screen, and every finding's reason and recommendation, in both
  languages; switch on any page.
- **Retrieval ready.** pgvector for embeddings, with tested patterns in the
  `document-verification` skill.
- **Agents that follow the same rules.** `AGENTS.md` holds the stack rules and the definition of
  done; skills cover UI design, minimal code, document checks, deployment and the pitch.
- **Quality gates.** `make check` (formatting, lint, types, tests) and `make check-ui` (two UI
  anti-slop detectors), run by CI on every push.
- **Scored like the jury.** The `hackathon-judge` skill rates the project against the official
  judging criteria (rubric in [docs/judging/rubric.md](docs/judging/rubric.md)), re-read from the
  hackathon's site each time; a scheduled workflow opens an issue when the organisers change them.
- **One-command Azure deploy.** Container Apps, PostgreSQL, Container Registry, AI Foundry and
  Keycloak through Terraform, with generated secrets.

## Stack

| Layer | Technology |
|---|---|
| Web | Next.js 16.4 (App Router, React 19.3, React Compiler, Cache Components), TypeScript, Tailwind CSS 4 |
| API | FastAPI, Python 3.13, Poetry, SQLAlchemy 2 (async), Alembic |
| Data | PostgreSQL 17 with pgvector |
| Sign-in | Keycloak 26 (OpenID Connect with PKCE); roles `client`, `reviewer`, `admin`; tokens in encrypted httpOnly cookies, checked by the API |
| AI | Any OpenAI-compatible API, switched in `.env` with `AI_PROVIDER=azure` or `AI_PROVIDER=bedrock` (AWS Bedrock API key); defaults to Azure AI Foundry `gpt-5-mini` and `text-embedding-3-small` |
| Local | Docker Compose |
| Cloud | Terraform: Azure Container Apps, PostgreSQL Flexible Server, Container Registry, AI Foundry, Keycloak |
| Quality | Ruff, mypy, pytest, ESLint, Prettier, Vitest, knip, impeccable and taste UI linters, GitHub Actions |

## Setup

### 1. Install these yourself

| Tool | Why | How |
|---|---|---|
| Git | Clone and commit | macOS: `xcode-select --install` · Ubuntu/WSL: `sudo apt install git` |
| Docker Desktop (Docker Engine on Linux) | Runs web, API, database and Keycloak | [docs.docker.com/get-docker](https://docs.docker.com/get-docker/) |
| WSL 2 with Ubuntu (Windows only) | Docker Desktop and the setup script run there | `wsl --install`, then clone inside WSL, not under `/mnt/c` |
| Homebrew (macOS only) | The setup script installs tools with it | [brew.sh](https://brew.sh) |
| An AI coding agent | Building the product | Claude Code, Codex, Antigravity, Kiro, Cursor, Copilot... |

### 2. Run the setup

```bash
git clone https://github.com/robery567/ai-engineering-project-template-azure.git
cd ai-engineering-project-template-azure
make setup
```

Or ask your agent: "Set up this project on my machine." Without `make`, run
`bash scripts/setup.sh`.

The setup installs any missing tool from the table below, with no admin password, then creates
`.env`, installs the web and API dependencies, and starts the stack on http://localhost:3000.
Sign in as `client`, `reviewer` or `admin` with the password `demo`.
`make doctor` reports what is installed without changing anything. Whatever needs you (Docker,
for example) is printed as "Needs you".

| Installed for you | Used for | To install it yourself instead |
|---|---|---|
| Node.js 22+ | Editor types, Next.js docs for agents, `make check-ui`, MCP servers | `brew install node` · [nodejs.org](https://nodejs.org/en/download) |
| Terraform 1.9+ | Azure deployment | `brew install hashicorp/tap/terraform` · [install guide](https://developer.hashicorp.com/terraform/install) |
| Azure CLI | Azure login and deployment | `brew install azure-cli` · Ubuntu/WSL: `curl -sL https://aka.ms/InstallAzureCLIDeb \| sudo bash` |
| Poetry 2 and Python 3.13 | Running the API outside Docker, editor support | `brew install poetry python@3.13` · [python-poetry.org](https://python-poetry.org/docs/#installation) |

macOS uses Homebrew. On Linux and WSL the tools go into `~/.local/bin`; add it to your `PATH` if
the setup says so.

### 3. Connect an AI provider

Choose the provider in `.env` with `AI_PROVIDER=azure` (`AZURE_AI_BASE_URL`, `AZURE_AI_API_KEY`)
or `AI_PROVIDER=bedrock` (`BEDROCK_API_KEY`, `BEDROCK_BASE_URL`, `BEDROCK_MODEL`)
([docs/ai-providers.md](docs/ai-providers.md) has ready-made blocks), run `docker compose up -d api`, then press **Run AI check** on http://localhost:3000/status.

## Working with your agent

1. Agents read `AGENTS.md` automatically (Claude Code through `CLAUDE.md`).
   [docs/agents.md](docs/agents.md) shows how each tool is wired.
2. Keep [PRODUCT.md](PRODUCT.md) current: users, the problem, the checks that matter, open
   decisions. Every agent reads it before product work.
3. Build in small vertical slices, and split work by area so two agents do not edit the same files.
4. Before you merge: `make check`, plus `make check-ui` and a look at a phone-sized window for UI
   work. [DESIGN.md](DESIGN.md) keeps everyone's screens consistent.

## Skills

| Skill | Use it for | Ask for example |
|---|---|---|
| `impeccable` | Designing, critiquing, auditing and polishing UI | "/impeccable critique the review page" |
| `design-taste-frontend` | Public pages such as a pitch landing page | "Use the taste skill for a landing page" |
| `ponytail`, `ponytail-review`, `ponytail-audit`, `ponytail-debt` | Smallest-change coding, diff review, repo audit, listing shortcuts | "/ponytail-review my changes" |
| `document-verification` | Extraction with citations, cross-document checks, OCR, Romanian IDs, pgvector | "Add a check that invoice totals match the contract" |
| `azure-deploy` | Deploying with Terraform and fixing deploy errors | "Deploy to Azure" |
| `hackathon-judge` | Scoring the project like the jury, against the official criteria re-read from the hackathon's site | "/hackathon-judge before the jury checkpoint" |
| `hackathon-pitch` | Build order, demo script, answers to the jury | "Prepare the 3-minute demo script" |

Claude Code and Kiro invoke skills with `/name`, Codex with `$name`; most agents also load them on
their own when a task matches.

## Commands

| Command | What it does |
|---|---|
| `make setup` / `make doctor` | Install what is missing / only report |
| `make up` / `make down` | Start or stop the stack; run `make up` again after every pull |
| `make reset-auth` | Re-import the `client`, `reviewer` and `admin` users and roles from `infra/keycloak/realm-app.json` |
| `make check` | Every API and web check |
| `make check-ui` | Impeccable on source and rendered pages, plus taste's linter |
| `make fix` | Formatting and autofixable lint |
| `make migration m="add documents"` | Alembic migration from `api/app/models.py` |
| `make gen-api` | Regenerate the web app's API types after an API change |
| `make criteria` | Re-read the hackathon's official rules, criteria and schedule and report changes |
| `make deploy` | Build, push and deploy to Azure ([docs/deploy-azure.md](docs/deploy-azure.md)) |
| `make help` | Everything else |

## Layout

```text
api/               FastAPI: app/ai/client.py (the only AI client), app/routes/, migrations/, tests/
                   app/verification/ (agents, checks registry, orchestrator, runner), app/pdf/,
                   app/ocr/ (scanned pages), app/personal_data/ (CNP detection, HMAC, masking),
                   app/documents/ (uploads, OCR jobs), app/projects/
web/               Next.js: src/app/[lang]/ (every page, in English and Romanian: home, projects,
                   admin/regulations, status), src/app/api/[...path] (proxy to the API),
                   src/app/auth and src/proxy.ts (sign-in, languages), src/i18n (dictionaries)
infra/keycloak/    Sign-in realm (users, roles, the web client) and the Azure image
infra/terraform/   Azure infrastructure, with offline tests
scripts/           setup.sh, deploy.sh, sync_agents.py
.agents/skills/    Skills; copies for Claude Code in .claude/ and Kiro in .kiro/
docs/              AI providers, sign-in, Azure deployment, agent wiring, judging rubric
AGENTS.md          Rules every agent reads
PRODUCT.md         Product brief
DESIGN.md          Design system
```

The browser only talks to Next.js. Server Components call FastAPI directly; client code goes
through `/api/*`, which Next.js forwards with the user's access token. On Azure the API is not
public at all.

## Troubleshooting

- **Port already in use:** set `WEB_PORT`, `API_PORT`, `DB_PORT` or `KEYCLOAK_PORT` in `.env`,
  then `make up`; after changing `WEB_PORT`, also `make reset-auth`.
- **Keycloak says "Invalid parameter: redirect_uri":** `make reset-auth`.
- **Pulled or added a dependency, or "Module not found":** `make up`. It rebuilds the images and
  gives the web container a fresh `node_modules`; the database is kept.
- **Fresh database:** `make reset-db`, then `make up`.
- **A tool is "not found" after setup on Linux or WSL:** add `~/.local/bin` to your `PATH`.

Third-party skills and fonts keep their licences: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
