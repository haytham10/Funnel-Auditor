#!/usr/bin/env python3
"""Stop a push that would carry a stale mirror of the CRM's select options.

`audit/airtable.py` and the two segment lists mirror a schema Airtable owns and
this repo does not. `main.py doc-check --live` compares them, but that check
needs `AIRTABLE_API_KEY`, and CI has none — so on the one path where it would
run automatically, it cannot.

The key does exist here, in the session. And the moment that matters is the
push: it is what creates or updates the PR, and it is the last point before the
mirror leaves this machine. So the check binds there.

**Why a substring test and not the `if:` filter.** A hook's `if:` uses
permission-rule syntax, which is prefix-matched — `Bash(git push*)` does not
match `git add -A && git commit -m ... && git push -u origin ...`, which is how
a commit-and-push is usually actually written. It would have missed the push
that introduced this file. Correctness first: this matches every Bash call and
returns in one `in` test when the command is not a push. Nothing heavier than
the interpreter itself is imported until a push is confirmed.

**Blocks on drift, allows on could-not-run.** These are opposite defaults from
the rest of the machine and the split is deliberate. Real drift is one line to
fix and nothing else can catch it, so it stops the push. But "Airtable is
unreachable" would otherwise hold every unrelated push in the repo hostage to
somebody else's outage, and the thing a stale mirror endangers is a *batch*, not
a merge — so that case warns loudly and gets out of the way. The warning is the
point: it must never be silent, or "it would have run if it could" is back.

Disable via /hooks if it is ever in the way.
"""

import json
import os
import sys

PUSH = "git push"


def emit(payload: dict) -> None:
    print(json.dumps(payload))
    sys.exit(0)


def allow(context: str) -> None:
    """Let the push through, telling the model what happened. Not user-facing."""
    emit({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                 "additionalContext": context}})


def warn(message: str) -> None:
    """Let the push through, but say so where a person will see it."""
    emit({"systemMessage": message,
          "hookSpecificOutput": {"hookEventName": "PreToolUse",
                                 "additionalContext": message}})


def deny(reason: str) -> None:
    emit({"systemMessage": "Push blocked: the CRM select options drifted.",
          "hookSpecificOutput": {"hookEventName": "PreToolUse",
                                 "permissionDecision": "deny",
                                 "permissionDecisionReason": reason}})


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
        sys.exit(0)

    command = (event.get("tool_input") or {}).get("command") or ""
    if PUSH not in command:
        sys.exit(0)

    root = os.environ.get("CLAUDE_PROJECT_DIR")
    if not root:
        from pathlib import Path
        root = str(Path(__file__).resolve().parent.parent.parent)
    sys.path.insert(0, root)

    try:
        from audit import airtable
        from outbound import doc_check
    except ImportError as exc:
        # A checkout without the dependencies installed is not a schema problem.
        warn(f"CRM schema check skipped: {exc}")

    if not airtable.available():
        warn("CRM schema check skipped: no AIRTABLE_API_KEY in this session, so "
             "the select-option mirrors in audit/airtable.py went unchecked.")

    try:
        findings = doc_check.check_airtable_selects(airtable.base_schema())
    except Exception as exc:                      # noqa: BLE001
        # Deliberately broad. Any failure to reach Airtable must produce a
        # visible warning and a push, never a traceback into the hook runner,
        # which would read as the hook being broken rather than the network.
        warn(f"CRM schema check could not run: {exc}. The mirrors in "
             f"audit/airtable.py went unchecked on this push.")

    if not findings:
        allow(f"CRM schema check: {len(doc_check.AIRTABLE_SELECTS)} select "
              f"field(s) matched the live base.")

    lines = "\n".join(f"  {f.as_line()}" for f in findings)
    deny(f"The CRM's select options no longer match the tuples that mirror "
         f"them, so this push would carry a stale mirror:\n\n{lines}\n\n"
         f"Fix the listed module (or the Airtable base), then run "
         f"`python main.py doc-check --live` to confirm before pushing again.")


if __name__ == "__main__":
    main()
