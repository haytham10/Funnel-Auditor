#!/usr/bin/env python3
"""
PreToolUse guard for mcp__Gmail__create_draft.

The trap it closes: Gmail auto-links any BARE domain or email address in a
draft body, rewriting e.g. `drsusankoruthu.com` into a
`https://www.google.com/url?q=...&source=gmail&ust=...` tracking redirect.
In a personal cold email that reads as a spam signal and kills the voice.
It has bitten a real Susan Koruthu draft; the rule is now code-enforced so
it can't recur.

Contract (Claude Code hook):
- reads the tool call as JSON on stdin (`tool_input.body`, `tool_input.htmlBody`)
- exit 0  -> allow the draft
- exit 2  -> BLOCK the draft; stderr is fed back so the model fixes the body

What counts as an offender: a bare domain (`name.tld`, no scheme) or a bare
email address sitting in the body text. Deliberate links written with an
explicit `http://`, `https://`, or `mailto:` scheme are ALLOWED (money-email
proof links are meant to be links) and are stripped before scanning. A small
allowlist covers bare proof domains that are known-intended.

Fixing a block: don't print the bare domain. Refer to the site by
description ("your old site", "the FAQ page"). Cold openers carry no links
at all; if a link is genuinely intended (a money email's proof), write it
with an explicit https:// scheme so it's unambiguous.

Fails OPEN only on an unreadable/unexpected payload (never bricks drafting);
the normal path with a body present always scans.
"""
from __future__ import annotations

import json
import os
import sys

# The scan rule lives in audit/draft_lint.py so this hook (Inbox 1 / Gmail
# MCP) and audit/gmail_gethaytham.create_draft (Inbox 2 / direct API) enforce
# the SAME copy rules — bare-link AND em-dash — and can never drift apart.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    from audit import draft_lint
except Exception:
    draft_lint = None  # if the import fails, fail open below — never brick drafting


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0  # unreadable payload -> fail open, never brick drafting

    if payload.get("tool_name") != "mcp__Gmail__create_draft":
        return 0
    if draft_lint is None:
        return 0  # module unavailable -> fail open

    tool_input = payload.get("tool_input") or {}
    parts = [tool_input.get("body") or "", tool_input.get("htmlBody") or ""]
    problems = draft_lint.scan("\n".join(parts))
    if not problems:
        return 0

    print(
        "BLOCKED: Gmail draft body fails a copy rule — " + "; ".join(problems) + "\n"
        "Fix: don't print bare addresses (refer to the site by description, e.g. "
        '"your old site"; cold openers carry no links, an intended proof link gets '
        "an explicit https:// scheme). Remove any em-dash.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
