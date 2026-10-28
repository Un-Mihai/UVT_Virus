#!/usr/bin/env python3
"""Copy .agents/skills to the folders Claude Code and Kiro read, and validate every skill.

.agents/skills is the source of truth: Codex, Antigravity, Cursor, Copilot, opencode, Zed and
other agents read it directly. Skills that exist only in a copy folder (for example one made with
Claude's skill-creator) are reported, never deleted. Run after adding or editing a skill:

    python3 scripts/sync_agents.py          copy and validate
    python3 scripts/sync_agents.py --check  change nothing; exit 1 if a copy is stale (CI)
"""

import argparse
import filecmp
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / ".agents" / "skills"
TARGETS = [ROOT / ".claude" / "skills", ROOT / ".kiro" / "skills"]
# Shipped by their authors as a separate build per tool (paths differ inside); refresh these from
# upstream instead of copying (see THIRD_PARTY_NOTICES.md).
VENDOR_BUILDS = {"impeccable"}
JUNK = {".DS_Store", "__pycache__"}
NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def frontmatter(skill_md: Path) -> dict[str, str]:
    """The top-level `key: value` pairs, with folded (`>`) values joined into one line."""
    lines = skill_md.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---" or "---" not in lines[1:]:
        return {}
    fields: dict[str, str] = {}
    key = None
    for line in lines[1 : lines.index("---", 1)]:
        if match := re.match(r"^([A-Za-z_-]+):\s*(.*)$", line):
            key, value = match.groups()
            fields[key] = "" if value in (">", ">-", "|", "|-") else value.strip().strip("\"'")
        elif key and line[:1] in (" ", "\t"):
            fields[key] = f"{fields[key]} {line.strip()}".strip()
    return fields


def problems(skill: Path) -> list[str]:
    skill_md = skill / "SKILL.md"
    if not skill_md.is_file():
        return [f"{skill}: no SKILL.md"]
    fields = frontmatter(skill_md)
    name, description = fields.get("name", ""), fields.get("description", "")
    errors = []
    if name != skill.name:
        errors.append(f"{skill}: name '{name}' must equal the folder name")
    if not NAME.match(name) or len(name) > 64:
        errors.append(f"{skill}: name must be 1-64 lowercase letters, digits and single hyphens")
    if not 1 <= len(description) <= 1024:
        errors.append(f"{skill}: description has {len(description)} characters (allowed 1-1024)")
    return errors


def files(tree: Path) -> list[Path]:
    return sorted(
        path.relative_to(tree)
        for path in tree.rglob("*")
        if path.is_file() and not JUNK & set(path.relative_to(tree).parts)
    )


def same_tree(source: Path, copy: Path) -> bool:
    return (
        copy.is_dir()
        and files(source) == files(copy)
        and all(filecmp.cmp(source / f, copy / f, shallow=False) for f in files(source))
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--check", action="store_true", help="report stale copies, change nothing")
    check = parser.parse_args().check

    skills = sorted(path for path in SOURCE.iterdir() if path.is_dir())
    errors = [error for skill in skills for error in problems(skill)]
    errors += [
        error
        for target in TARGETS
        for name in VENDOR_BUILDS
        if (target / name).is_dir()
        for error in problems(target / name)
    ]

    stale = []
    for target in TARGETS:
        for skill in skills:
            copy = target / skill.name
            if skill.name in VENDOR_BUILDS or same_tree(skill, copy):
                continue
            stale.append(copy)
            if not check:
                shutil.rmtree(copy, ignore_errors=True)
                shutil.copytree(skill, copy, ignore=shutil.ignore_patterns(*JUNK))

    extras = [
        copy
        for target in TARGETS
        if target.is_dir()
        for copy in sorted(target.iterdir())
        if copy.is_dir() and copy.name not in VENDOR_BUILDS and not (SOURCE / copy.name).is_dir()
    ]
    for copy in extras:
        print(
            f"only in {copy.relative_to(ROOT)}: move it to .agents/skills to share it with every agent"
        )
    for error in errors:
        print(f"invalid: {error}", file=sys.stderr)
    for copy in stale:
        print(f"{'stale' if check else 'updated'}: {copy.relative_to(ROOT)}")
    if not errors and not stale:
        print(f"{len(skills)} skills valid; copies up to date in {len(TARGETS)} folders.")
    return 1 if errors or (check and stale) else 0


if __name__ == "__main__":
    sys.exit(main())
