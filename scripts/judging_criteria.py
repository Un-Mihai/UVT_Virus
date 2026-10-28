#!/usr/bin/env python3
"""Check the hackathon's official rules, judging criteria and schedule for changes.

The hackathon-judge skill scores the project with docs/judging/rubric.md, which is built from the
organiser's pages. This script reads those pages, keeps the parts about rules, judging and the
hackathon schedule, and compares them with docs/judging/sources.lock (one SHA-256 per part), so
criteria the organisers add or change later are noticed. The text itself is cached locally in
.cache/judging/ (git-ignored) to show what changed; the repo stores only fingerprints.

    python3 scripts/judging_criteria.py          report changes, update the lock and the cache
    python3 scripts/judging_criteria.py --show   also print the current official text
    python3 scripts/judging_criteria.py --check  change nothing; exit 3 if a page changed (CI)

Exit codes: 0 unchanged, 3 changed, 2 a page could not be fetched.
"""

import argparse
import datetime
import difflib
import hashlib
import html
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCK = ROOT / "docs" / "judging" / "sources.lock"
CACHE = ROOT / ".cache" / "judging"
USER_AGENT = "Mozilla/5.0 (compatible; hackathon-team-criteria-check)"
# title, url, the line that starts the part to keep, the line that ends it, keep that last line
SOURCES = [
    ("Rulebook", "https://nexxtsummit.com/rulebook", "Hackathon Rulebook", "Last updated:", True),
    (
        "Agenda: hackathon days",
        "https://nexxtsummit.com/agenda",
        "AI HACKATHON |",
        "AI Summit Main Stage",
        False,
    ),
    (
        "Hackathon page",
        "https://nexxtsummit.com/hackathon",
        "A two-day AI hackathon",
        "Best mentors in the industry",
        False,
    ),
]
# Used when a page's layout changes and the markers above are gone.
KEYWORDS = re.compile(
    r"criteri|evaluat|jury|juror|judg|scor|weight|pitch|demo|present|submi|deadline|checkpoint|final",
    re.IGNORECASE,
)


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return str(response.read().decode("utf-8", errors="replace"))
    except OSError:
        if not shutil.which("curl"):
            raise
        # Some Python installs ship without CA certificates; curl uses the system's.
        command = ["curl", "-fsSL", "--max-time", "30", "-A", USER_AGENT, url]
        return subprocess.run(command, capture_output=True, text=True, check=True).stdout


def visible_lines(page: str) -> list[str]:
    page = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", page)
    page = re.sub(r"(?i)<(br|/p|/div|/li|/h[1-6]|/section|/tr)[^>]*>", "\n", page)
    text = html.unescape(re.sub(r"<[^>]+>", " ", page))
    return [
        line for line in (re.sub(r"\s+", " ", raw).strip() for raw in text.splitlines()) if line
    ]


def part(lines: list[str], start: str, end: str, keep_end: bool) -> list[str] | None:
    first = next((i for i, line in enumerate(lines) if start in line), None)
    if first is None:
        return None
    last = next((i for i in range(first + 1, len(lines)) if end in lines[i]), None)
    if last is None:
        return None
    return lines[first : last + 1 if keep_end else last]


def official_text(url: str, start: str, end: str, keep_end: bool) -> str:
    lines = visible_lines(fetch(url))
    kept = part(lines, start, end, keep_end)
    if kept is None:
        kept = ["(The page layout changed: keyword matches from the whole page.)"]
        kept += [line for line in lines if KEYWORDS.search(line)]
    return "\n".join(kept) + "\n"


def cache_file(title: str) -> Path:
    return CACHE / (re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") + ".txt")


def read_lock() -> dict[str, tuple[str, str]]:
    """title -> (sha256, date it was recorded)"""
    if not LOCK.exists():
        return {}
    entries = {}
    for line in LOCK.read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            digest, date, title, _url = line.split("\t")
            entries[title] = (digest, date)
    return entries


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--check", action="store_true", help="report changes, write nothing")
    parser.add_argument("--show", action="store_true", help="print the current official text")
    args = parser.parse_args()

    try:
        live = {
            title: (url, official_text(url, start, end, keep_end))
            for title, url, start, end, keep_end in SOURCES
        }
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"Could not fetch the official pages ({error}).", file=sys.stderr)
        print(
            "Score with docs/judging/rubric.md as it is and say the check was offline.",
            file=sys.stderr,
        )
        return 2

    if args.show:
        for title, (url, text) in live.items():
            print(f"===== {title} ({url}) =====\n{text}")

    locked = read_lock()
    today = datetime.datetime.now(datetime.UTC).date().isoformat()
    changed = []
    lock_lines = ["# Generated by scripts/judging_criteria.py: SHA-256 of each official page part."]
    for title, (url, text) in live.items():
        digest = hashlib.sha256(text.encode()).hexdigest()
        known_digest, known_date = locked.get(title, ("", today))
        if digest != known_digest:
            changed.append(title)
            known_date = today
            previous = cache_file(title)
            if previous.exists():
                diff = difflib.unified_diff(
                    previous.read_text(encoding="utf-8").splitlines(),
                    text.splitlines(),
                    "before",
                    "now",
                    lineterm="",
                )
                print(f"CHANGED: {title} ({url})\n" + "\n".join(diff))
            else:
                print(
                    f"CHANGED: {title} ({url}). No earlier copy on this machine: read it with --show."
                )
        lock_lines.append(f"{digest}\t{known_date}\t{title}\t{url}")
        if not args.check:
            CACHE.mkdir(parents=True, exist_ok=True)
            cache_file(title).write_text(text, encoding="utf-8")

    if not changed:
        dates = ", ".join(f"{title} since {date}" for title, (_, date) in sorted(locked.items()))
        print(f"Official rules, criteria and schedule unchanged ({dates}).")
        return 0
    if not args.check:
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text("\n".join(lock_lines) + "\n", encoding="utf-8")
        print(
            f"\nUpdated {LOCK.relative_to(ROOT)}. If the criteria changed, update docs/judging/rubric.md."
        )
    return 3


if __name__ == "__main__":
    sys.exit(main())
