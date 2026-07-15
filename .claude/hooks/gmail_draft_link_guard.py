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
import re
import sys

# Bare proof domains that are deliberately used and should not trip the guard.
# Anything written with an explicit https:// scheme is already allowed, so keep
# this minimal — it's only for domains habitually written bare.
ALLOWLIST = {
    "haytham-sys.netlify.app",
}

# Common TLDs we actually see in this pipeline (coach sites, UAE/GCC, socials).
# Curated rather than "any TLD" to keep false positives near zero.
_TLDS = (
    "com|net|org|io|co|me|ai|app|dev|site|online|xyz|info|biz|store|link|tech|"
    "live|blog|page|so|ae|sa|qa|bh|om|kw|eg|uk|de|fr|es|nl|in|us|ca|au"
)

_SCHEME_URL = re.compile(r"(?:https?://|mailto:)\S+", re.IGNORECASE)
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_BARE_DOMAIN = re.compile(
    r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+(?:" + _TLDS + r")\b",
    re.IGNORECASE,
)


def scan(text: str) -> list[str]:
    """Return bare domains / emails that Gmail would auto-link. Empty = clean."""
    if not text:
        return []
    # Deliberate, scheme-qualified links are fine — remove them before scanning.
    work = _SCHEME_URL.sub(" ", text)

    offenders: list[str] = []

    emails = _EMAIL.findall(work)
    offenders.extend(emails)
    # Drop emails before the domain pass so their domain half isn't double-flagged.
    work = _EMAIL.sub(" ", work)

    for m in _BARE_DOMAIN.finditer(work):
        token = m.group(0)
        if token.lower() in ALLOWLIST:
            continue
        offenders.append(token)

    # De-dupe, preserve order.
    seen: set[str] = set()
    unique: list[str] = []
    for tok in offenders:
        low = tok.lower()
        if low not in seen:
            seen.add(low)
            unique.append(tok)
    return unique


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0  # unreadable payload -> fail open, never brick drafting

    if payload.get("tool_name") != "mcp__Gmail__create_draft":
        return 0

    tool_input = payload.get("tool_input") or {}
    parts = [tool_input.get("body") or "", tool_input.get("htmlBody") or ""]
    offenders = scan("\n".join(parts))
    if not offenders:
        return 0

    listed = ", ".join(offenders)
    print(
        "BLOCKED: Gmail draft body contains a bare domain/email that Gmail will "
        f"auto-link into a google.com/url redirect: {listed}\n"
        "Fix: don't print the bare address. Refer to the site by description "
        '("your old site", "the FAQ page"). Cold openers carry no links at all. '
        "If a link is genuinely intended (a money-email proof link), write it "
        "with an explicit https:// scheme.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
