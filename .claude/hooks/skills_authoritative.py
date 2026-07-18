#!/usr/bin/env python3
"""
SessionStart hook — pin THIS repo's `.claude/skills/` as the authoritative
skill set for the session.

The trap it closes: in a fresh managed/web session Claude may answer a
skill's job from a REMEMBERED or globally-installed copy of that skill
(training memory, a marketplace version) instead of the version committed
here — and the two can drift, so the session runs stale logic ("wrong skill
version loaded"). This hook fingerprints every SKILL.md actually on disk and
injects that inventory as session context, so the repo is the single source
of truth from the first turn: the fingerprint changes the moment a file does,
which is exactly the signal a remembered copy can't provide.

Contract (Claude Code SessionStart hook):
- receives the session payload as JSON on stdin (unused here)
- prints JSON on stdout whose `hookSpecificOutput.additionalContext` is added
  to the session context
- exit 0 always. Fails OPEN (emits nothing) on any error — it must never
  block a session from starting.

The inventory is name + a short content hash (first 12 hex of sha256 over the
raw file) + mtime date, one line per skill. The hash is a stable, diffable
"which version" marker: quote it if you need to confirm you are on the repo's
copy, and re-read the SKILL.md from disk rather than from memory.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import date
from pathlib import Path

# .claude/hooks/skills_authoritative.py -> repo root is two parents up from
# .claude, i.e. three parents up from this file.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SKILLS_DIR = _REPO_ROOT / ".claude" / "skills"


def _inventory() -> list[str]:
    lines: list[str] = []
    for skill_md in sorted(_SKILLS_DIR.glob("*/SKILL.md")):
        try:
            raw = skill_md.read_bytes()
        except OSError:
            continue
        digest = hashlib.sha256(raw).hexdigest()[:12]
        try:
            mtime = date.fromtimestamp(skill_md.stat().st_mtime).isoformat()
        except OSError:
            mtime = "unknown"
        lines.append(f"  - {skill_md.parent.name}: v={digest} (updated {mtime})")
    return lines


def main() -> int:
    try:
        _ = sys.stdin.read()  # drain the payload; nothing in it is needed
    except Exception:
        pass

    try:
        lines = _inventory()
    except Exception:
        return 0  # fail open — never block a session from starting

    if not lines:
        return 0

    context = (
        "AUTHORITATIVE SKILLS — this repo's committed `.claude/skills/` is the "
        "single source of truth for every skill below. When one of these skills "
        "applies, read its SKILL.md (and referenced files) FROM DISK and follow "
        "that; do NOT answer from a remembered or globally-installed copy, which "
        "may be an older version. Each line's `v=` is a content fingerprint of "
        "the on-disk SKILL.md — if it differs from what you recall, the file on "
        "disk wins.\n" + "\n".join(lines)
    )
    out = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }
    try:
        print(json.dumps(out))
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
