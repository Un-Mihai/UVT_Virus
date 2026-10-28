# Third-party notices

This starter includes third-party work under its original licences. Each vendored skill folder
also carries its own `LICENSE` (and `NOTICE.md` where the project has one).

| Component | Version | Licence | Where |
|---|---|---|---|
| [Impeccable](https://github.com/pbakaus/impeccable) by Paul Bakaus | `skill-v4.7.0` (aeeb3d8) | Apache-2.0 | `.agents/skills/impeccable/`, `.claude/skills/impeccable/`, `.kiro/skills/impeccable/`, `.claude/agents/impeccable-*.md`, hooks in `.claude/settings.json` and `.codex/hooks.json` |
| [Taste skill](https://github.com/Leonxlnx/taste-skill) by Leonxlnx | `v2.1.5` (12af471) | MIT | `.agents/skills/design-taste-frontend/` and its copies |
| [Ponytail](https://github.com/DietrichGebert/ponytail) by DietrichGebert | `v5.3.2` (16352ac) | MIT | `.agents/skills/ponytail*/` and copies; the "Code quality" rules in `AGENTS.md` are adapted from its `AGENTS.md` |
| [Atkinson Hyperlegible Next](https://github.com/googlefonts/atkinson-hyperlegible-next) and Mono | Google Fonts release | SIL Open Font License 1.1 | `web/src/app/fonts/` |
| Next.js agent rules block | Next.js 16.4.3 | MIT | `web/AGENTS.md`, between the `nextjs-agent-rules` markers |

Impeccable's NOTICE: its iOS and Android platform references are distilled from
[ehmo/platform-design-skills](https://github.com/ehmo/platform-design-skills) (MIT).

Impeccable's launcher (`scripts/impeccable`) downloads its detector engine for your platform from
the project's GitHub releases on first use, verifies its SHA-256, and caches it in
`~/.impeccable`.

## Updating the vendored skills

```bash
git clone --depth 1 --branch <tag> https://github.com/pbakaus/impeccable /tmp/impeccable
for tool in .agents .claude .kiro; do
  rm -rf "$tool/skills/impeccable"
  cp -R "/tmp/impeccable/$tool/skills/impeccable" "$tool/skills/impeccable"
  cp /tmp/impeccable/LICENSE /tmp/impeccable/NOTICE.md "$tool/skills/impeccable/"
done
cp /tmp/impeccable/.claude/agents/impeccable-*.md .claude/agents/
```

For taste and ponytail, replace the folders under `.agents/skills/` from the new tag
(`skills/taste-skill` becomes `design-taste-frontend`; ponytail's `skills/<name>`), keep their
`LICENSE`, then run `make sync-agents`.
