# How the agent harness is wired

One set of instructions and skills, read by every coding agent the team uses.

| File or folder | What it is | Read by |
|---|---|---|
| `AGENTS.md` | Always-on rules: stack, commands, code and UI quality, definition of done | Codex, Antigravity, Kiro, Cursor, Copilot, opencode, Amp, Zed, Junie, Devin/Windsurf |
| `CLAUDE.md` | Imports `AGENTS.md` (`@AGENTS.md`) plus Claude notes | Claude Code |
| `web/AGENTS.md`, `web/CLAUDE.md` | Next.js 16.4 notes; `next dev` keeps its managed block current | Agents working inside `web/` |
| `PRODUCT.md`, `DESIGN.md` | Product brief and design system | Every agent via AGENTS.md; impeccable loads them itself |
| `.agents/skills/` | Skills, the source of truth | Codex, Antigravity, Cursor, Copilot, Gemini CLI, opencode, Amp, Zed, Junie |
| `.claude/skills/`, `.kiro/skills/` | Copies of the skills | Claude Code, Kiro |
| `.mcp.json`, `.cursor/mcp.json`, `.kiro/settings/mcp.json`, `.agents/mcp_config.json`, `.gemini/settings.json`, `.codex/config.toml`, `opencode.json` | The same two MCP servers (Next.js runtime errors and docs, a Playwright browser) in each tool's format | Claude Code and VS Code, Cursor, Kiro, Antigravity, Gemini CLI, Codex (trusted projects), opencode |
| `.claude/settings.json`, `.codex/hooks.json` | Command permissions and impeccable's design-detector hooks | Claude Code, Codex |
| `.gemini/settings.json` | Makes Gemini CLI read `AGENTS.md` | Gemini CLI |

Deliberately absent: `.cursorrules`, `.windsurfrules`, `.clinerules`, `.rules` and
`.github/copilot-instructions.md`. Zed reads only the first instruction file it finds, and those
names come before `AGENTS.md` in its list.

## Per tool

- **Claude Code:** skills are slash commands (`/impeccable audit`, `/ponytail-review`). The
  impeccable hook checks UI files after each edit; `/impeccable hooks off` turns it off. Approve
  the MCP servers once when asked.
- **Codex:** mark the project as trusted so `.codex/config.toml` and `.codex/hooks.json` load,
  then approve the hooks in `/hooks`. Invoke skills with `$impeccable` or pick them in `/skills`.
- **Antigravity:** reads `AGENTS.md`, `.agents/skills/` and `.agents/mcp_config.json`. Use its
  built-in browser to look at pages.
- **Kiro:** `AGENTS.md` is always included and skills come from `.kiro/skills/`. For a larger
  feature, Kiro's spec mode (requirements, design, tasks) fits the plan-first rule well.
- **Cursor, Copilot, opencode, Zed:** read `AGENTS.md` and `.agents/skills/` without setup.
- **Gemini CLI:** Google moved free and individual users to the Antigravity CLI (`agy`) in June
  2026; it reads the same files.

## Changing skills

1. Edit or add `.agents/skills/<name>/SKILL.md` (frontmatter `name` must equal the folder name,
   description up to 1,024 characters).
2. `make sync-agents` copies it to `.claude/skills/` and `.kiro/skills/` and validates every
   skill. CI runs `python3 scripts/sync_agents.py --check`.

Impeccable ships a separate build per tool, so its three copies are refreshed from upstream rather
than synced; see THIRD_PARTY_NOTICES.md for versions and how to update.

## Keeping instructions useful

- Keep `AGENTS.md` short. Every line is read on every task: put rules there only when an agent
  would get them wrong without being told. Workflows go into skills.
- When an agent repeats a mistake, add one line about it to `AGENTS.md` in the same change as the
  fix.
