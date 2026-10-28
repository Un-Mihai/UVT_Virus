<!-- BEGIN:nextjs-agent-rules -->

## This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

## This app

The repo-root AGENTS.md applies here too (stack, commands, UI rules, definition of done).

- `src/app/status/` is the stack diagnostics page. `/` redirects there (`next.config.ts`) until
  the product has a home page: delete the redirect and add `src/app/page.tsx`.
- Every page and `/api` call requires a signed-in user (`src/proxy.ts`, `src/app/auth/`); see
  `/docs/auth.md`. Read the user on the server from the session cookie, as
  `src/app/account-bar.tsx` does; tokens never reach Client Components.
- Client Components call FastAPI with `@/lib/api/browser`, everything on the server with
  `@/lib/api/server`. Both are typed from `src/lib/api/schema.d.ts` (`npm run gen:api`).
- Colours, fonts and radii come from tokens in `src/app/globals.css`, documented in `/DESIGN.md`.
