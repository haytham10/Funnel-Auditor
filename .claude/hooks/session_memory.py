#!/usr/bin/env python3
"""
SessionStart hook — load cross-session project memory into a fresh session.

The managed container is ephemeral and starts with no memory of prior
sessions. Live pipeline STATE survives in Notion and CODE changes survive in
git, but the NARRATIVE tying sessions together — ops events, decisions,
gotchas, open follow-ups — has no home unless it is written down. This hook
surfaces that narrative automatically at the top of every session:

  - the most recent entries from docs/journal.md (the hand-written log), and
  - the last few git commits (what changed, straight from history).

so the session boots already caught up instead of cold.

Contract (Claude Code SessionStart hook):
- receives the session payload as JSON on stdin (unused here)
- prints JSON on stdout whose `hookSpecificOutput.additionalContext` is added
  to the session context
- exit 0 always. Fails OPEN (emits nothing) on any error — it must never
  block a session from starting.

Writing memory is a human/agent habit (see docs/journal.md + CLAUDE.md): this
hook is the READ side only, and it is intentionally read-only — it never
writes, commits, or pushes.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

# .claude/hooks/session_memory.py -> repo root is three parents up.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_JOURNAL = _REPO_ROOT / "docs" / "journal.md"

_MAX_ENTRIES = 3       # most-recent journal blocks to surface
_MAX_JOURNAL_CHARS = 2000  # hard cap so a long entry can't flood context
_GIT_LOG_COUNT = 8


def _recent_journal() -> str:
    """The newest `_MAX_ENTRIES` `## ` blocks from the journal, capped in size.

    The journal is newest-first, so the wanted blocks are the first ones after
    the file's `---` separator. Everything above the first `## ` (the format
    preamble) is skipped.
    """
    try:
        text = _JOURNAL.read_text()
    except OSError:
        return ""
    lines = text.splitlines()
    # Entries live below the `---` rule that closes the format preamble; the
    # preamble itself contains a fenced `## ` template that must NOT be read as
    # an entry. Anchor on the first standalone `---`, then take blocks after it.
    sep = next((i for i, ln in enumerate(lines) if ln.strip() == "---"), None)
    body_lines = lines[sep + 1:] if sep is not None else lines
    start = next((i for i, ln in enumerate(body_lines) if ln.startswith("## ")), None)
    if start is None:
        return ""
    lines = body_lines
    kept: list[str] = []
    seen = 0
    for ln in lines[start:]:
        if ln.startswith("## "):
            seen += 1
            if seen > _MAX_ENTRIES:
                break
        kept.append(ln)
    body = "\n".join(kept).strip()
    if len(body) > _MAX_JOURNAL_CHARS:
        body = body[:_MAX_JOURNAL_CHARS].rstrip() + "\n… (truncated — see docs/journal.md)"
    return body


def _recent_commits() -> str:
    try:
        out = subprocess.run(
            ["git", "log", f"-{_GIT_LOG_COUNT}", "--pretty=format:%h %ad %s", "--date=short"],
            cwd=str(_REPO_ROOT), capture_output=True, text=True, timeout=5,
        )
    except Exception:
        return ""
    return out.stdout.strip() if out.returncode == 0 else ""


def main() -> int:
    try:
        _ = sys.stdin.read()  # drain payload; nothing in it is needed
    except Exception:
        pass

    try:
        journal = _recent_journal()
        commits = _recent_commits()
    except Exception:
        return 0  # fail open — never block a session from starting

    if not journal and not commits:
        return 0

    sections = [
        "PROJECT MEMORY (cross-session) — you start each session with no memory "
        "of prior ones; this is the recent narrative so you are not starting "
        "cold. Notion holds live pipeline STATE (query it for where leads are); "
        "this is the story of what was done and decided. Full log: "
        "docs/journal.md. When you finish work worth remembering, add an entry "
        "at the top of that file and commit + push it."
    ]
    if journal:
        sections.append("Recent journal entries:\n" + journal)
    if commits:
        sections.append("Recent commits:\n" + commits)

    out = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "\n\n".join(sections),
        }
    }
    try:
        print(json.dumps(out))
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
