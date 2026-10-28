# AGENTS.md

Instructions for every AI coding agent working in this repo (Claude Code, Codex, Antigravity,
Kiro, Cursor, Copilot, opencode, Zed...). Humans start with README.md.

## Product

Read PRODUCT.md before product work: what we build, for whom, and which decisions are still
open. When the team decides something, record it there in the same change.

## Stack

- `web/`: Next.js 16.4 (App Router, React 19.3, React Compiler, Cache Components, Tailwind CSS 4,
  TypeScript). The browser only talks to Next.js: `web/src/app/api/[...path]/route.ts` forwards
  `/api/*` to FastAPI, and Server Components call FastAPI through `web/src/lib/api/server.ts`.
- `api/`: FastAPI on Python 3.13 with Poetry, SQLAlchemy 2 (async, asyncpg), Alembic, pgvector.
- Database: PostgreSQL 17 + pgvector, in Docker locally and Azure Flexible Server in the cloud.
- Sign-in: Keycloak 26 (OpenID Connect), realm in `infra/keycloak/realm-app.json`; see
  `docs/auth.md`.
- `infra/terraform/`: Azure Container Apps, Container Registry, PostgreSQL, AI Foundry, Keycloak.
- AI: any OpenAI-compatible endpoint, chosen only by environment variables (`.env.example`).
  `AI_PROVIDER=azure` uses `AZURE_AI_BASE_URL` and `AZURE_AI_API_KEY`; `AI_PROVIDER=bedrock`
  uses `BEDROCK_API_KEY`, `BEDROCK_BASE_URL` and `BEDROCK_MODEL`. Both route only through
  `AIClient` (`api/app/ai/client.py`).

## Setup on a new machine

In a fresh clone, or when a command is missing, run `make doctor` (`bash scripts/setup.sh
--check`) first; it changes nothing. If it reports missing tools, run `make setup` (`bash
scripts/setup.sh`): it installs Node.js, Terraform, the Azure CLI and Poetry (Homebrew on macOS,
`~/.local` without sudo on Linux and WSL), creates `.env`, installs dependencies and starts the
stack. It never installs Docker, Git, WSL or Homebrew and never uses sudo. Pass every line it
prints as "Needs you" to the human word for word, and do not try to work around it.

## Commands

Everything runs in Docker; `make` targets are shortcuts for the commands shown.

| Task | Command |
|---|---|
| Check the machine, then install what is missing | `make doctor`, then `make setup` |
| Start the stack (web :3000, api :8000, keycloak :8080, db :5432), also after a pull | `make up` |
| All checks: run before you say a task is done | `make check` |
| API checks (format, lint, mypy, pytest) | `docker compose exec api poe check` |
| Web checks (prettier, eslint, tsc, vitest, knip) | `docker compose exec web npm run check` |
| UI anti-slop scan (impeccable + taste linters) | `make check-ui` |
| Fix formatting and autofixable lint | `make fix` |
| New migration after editing `api/app/models.py` | `make migration m="what changed"` |
| Refresh web types after any API change | `make gen-api` |
| Logs | `docker compose logs -f api web` |

Use the `make` targets that write files (`fix`, `migration`, `gen-api`): they run as the current
user, so Linux and WSL hosts do not end up with root-owned files. Without `make`, copy the command
from the Makefile.

## Rules that are not obvious

### Next.js 16.4 is newer than your training data

APIs and conventions differ from what you remember. Before writing Next.js code, read the
relevant guide in `web/node_modules/next/dist/docs/`. If `web/node_modules` does not exist on the
host, run `npm install` in `web/` (editors need it too), or read the same files in the container:
`docker compose exec web cat /app/node_modules/next/dist/docs/<path>`. In particular:

- Cache Components are on. Request-time data (uncached `fetch`, the API client) must sit inside
  `<Suspense>` or be cached with `"use cache"` plus `cacheLife`. The dev overlay names the fix.
- `middleware.ts` is now `proxy.ts`; `params` and `searchParams` are Promises; `PageProps`,
  `LayoutProps` and `RouteContext` are global type helpers.
- `NEXT_PUBLIC_*` values are frozen at build time. Server code reads `process.env` at request time,
  which is why the browser never calls FastAPI directly.

### API

- Every AI request goes through `AIClient` (`api/app/ai/client.py`). Never construct an OpenAI or
  Anthropic client elsewhere. It enforces `AI_DAILY_BUDGET_USD`, fails over to the second account,
  and records tokens and cost in `ai_calls`.
- Settings come only from environment variables via `api/app/config.py`. A new setting goes into
  `Settings`, `.env.example` and, if deployed, `infra/terraform/apps.tf` in the same change.
- Structured output: pass a Pydantic model to `AIClient.complete`. Keep schemas plain: Azure's
  strict mode rejects `pattern`, `format`, `minLength`, `minimum`, `minItems`. Validate after
  parsing, in code.
- GPT-5-family models reject `temperature` and `max_tokens`; send neither.
- Numbers, dates, sums and cross-document comparisons are computed in Python, never asked of the
  model. The model extracts and quotes; code decides. See the `document-verification` skill.
- A schema change is `models.py` plus a reviewed Alembic migration in the same change. Never edit
  a migration that has already run. Two people adding migrations at once creates two heads:
  `alembic merge heads`.
- Tests run against the real `app_test` database and a fake AI provider (`tests/conftest.py`).
  Tests never call a real provider.
- Regulation rules are stored per project type with a `verification_scope` of `"client"` or
  `"reviewer"`; the two scopes never share rules.
- Role-based confidence filtering on findings: `client` receives only client-scope findings with
  `confidence >= CLIENT_CONFIDENCE_THRESHOLD` (e.g. `0.85`); `reviewer` receives reviewer-scope
  findings with `confidence >= REVIEWER_CONFIDENCE_THRESHOLD` (e.g. `0.55`).

### Sign-in

- Every `/api` route needs a signed-in user: take `user: CurrentUser` (`app/auth.py`) or give
  the router `dependencies=[Depends(current_user)]`. Only `/health` is public.
- Check roles in the API (`user.roles`), not only by hiding buttons. The roles are `client`,
  `reviewer` and `admin`; every API route enforces them through `user.roles`.
- Tokens stay on the server, in encrypted httpOnly cookies. Never pass one to a Client
  Component, `NEXT_PUBLIC_*` or browser storage.
- Demo users `client`, `reviewer` and `admin` (each with the role of the same name in
  `infra/keycloak/realm-app.json`), password `demo`. After editing `realm-app.json`, run
  `make reset-auth`. API tests sign their own tokens (`make_client`, `make_token`).
- To call the running app from the shell, sign in with the wrapper: `node scripts/signed_in.mjs
  http://localhost:3000 curl -s http://localhost:3000/api/me`.

### Web

- Tailwind's default palette is switched off. Use the semantic tokens from
  `web/src/app/globals.css` (`bg-surface`, `text-ink-2`, `border-line`, `bg-accent`, `text-bad`).
  New tokens go into `globals.css` and `DESIGN.md` together.
- API types come from `npm run gen:api` (`web/src/lib/api/schema.d.ts`). Never hand-write them.

## Code quality: ponytail rules

Adapted from [ponytail](https://github.com/DietrichGebert/ponytail) (MIT). The skills
`ponytail`, `ponytail-review`, `ponytail-audit` and `ponytail-debt` go deeper.

You are a lazy senior developer. The best code is the code never written. Solve the whole problem
with the least new code. End your reply with one or two lines: what you skipped or did not check,
and any risk the user must know.

Before you write, read the task and the code it touches. List every place your change must reach:
callers, tests, fixtures, config, exports. That is scope. Extra features are not.

Take the first option that fully works:

1. Does it need to exist? Skip features, options and flexibility nobody asked for, and name them.
2. Already in this codebase (a helper, component, pattern)? Use it the way the surrounding code does.
3. Standard library or a platform feature? Use it, unless the project has its own.
4. An installed dependency? Use it. Never add a dependency for a few lines.
5. Otherwise, the minimum code that works.

- No abstraction, wrapper, option, config or "for later" code nobody asked for. Deletion beats
  addition. Keep the structure the codebase already has.
- Comment only the why the code cannot show, in one line.
- Bug fix: grep every caller of the function you touch, then fix the root cause once.
- New non-trivial logic (a branch, a parser, money, security) gets one small test.
- A shortcut with a known limit gets `# shortcut: <the limit>, <when to upgrade>`.
- Never cut: validation at trust boundaries, error handling that prevents data loss, security,
  accessibility, anything the user asked for.

## UI quality

- Before UI work, read `PRODUCT.md` and `DESIGN.md`, then use the `impeccable` skill. App screens
  are its Operate mode: familiar patterns, one sans family, restrained colour, dense and calm.
- Use `design-taste-frontend` only for public pages (a landing page for the pitch). Where both
  skills could apply, impeccable decides for app screens and taste decides for public pages.
- Never: gradient text, a label or eyebrow above a heading, same-size icon cards as the page
  structure, nested cards, emoji as icons, purple-to-blue gradients, decorative glass or blur,
  placeholder copy (lorem ipsum, "John Doe", made-up metrics).
- Every interactive element has hover, focus-visible, disabled and loading states; every list has
  an empty state that says what to do next; errors name the problem and the recovery.
- A UI task is done when `make check-ui` passes and you have looked at the rendered page at 390px
  and 1440px wide, in light and dark mode.

## Definition of done

1. `make check` passes (and `make check-ui` for UI work).
2. New logic has a test; a fixed bug has a test that failed before the fix.
3. PRODUCT.md, DESIGN.md and `.env.example` reflect any decision, token or setting you added.
4. Your final message says what changed and what you did not check.

## Skills

Skills live in `.agents/skills/`. Claude Code reads copies in `.claude/skills/` and Kiro in
`.kiro/skills/`: edit `.agents/skills/` and run `python3 scripts/sync_agents.py`.

| Skill | Use it for |
|---|---|
| `impeccable` | Designing, critiquing, auditing or polishing any UI; also writes DESIGN.md |
| `design-taste-frontend` | Public-facing pages such as a pitch landing page |
| `ponytail`, `ponytail-review`, `ponytail-audit`, `ponytail-debt` | Smallest-change coding, diff review, repo audit, listing `shortcut:` debt |
| `document-verification` | Extracting facts from documents, cross-checks, citations, OCR, Romanian identifiers |
| `azure-deploy` | Deploying to Azure with Terraform on student subscriptions, and fixing deploy errors |
| `hackathon-judge` | Scoring the project against the official judging criteria, re-read from the organiser's pages, before every checkpoint |
| `hackathon-pitch` | Build order, demo script, the cost and responsible-AI answers |

## Safety

- Never read, print or commit `.env`, `infra/terraform/terraform.tfvars`, `*.tfstate*` or
  Terraform's sensitive outputs: they hold keys and passwords. Ask the human to check a value
  instead.
- Never run `terraform apply`, `terraform destroy`, `make deploy` or any `az` command that changes
  resources unless a human asked for it in this session.
- Never drop tables or delete data outside a reviewed migration.
