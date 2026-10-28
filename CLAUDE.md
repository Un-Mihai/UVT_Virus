@AGENTS.md

## Claude Code

- Skills are in `.claude/skills/` (synced copies of `.agents/skills/`); invoke them as `/impeccable`,
  `/ponytail-review`, `/document-verification` and so on.
- The impeccable design detector runs as a hook after UI edits and at the end of a turn
  (`.claude/settings.json`); act on its findings. `/impeccable hooks off` disables it.
- MCP servers for Next.js runtime errors and a browser are in `.mcp.json`; approve them once.
