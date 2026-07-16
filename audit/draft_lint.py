"""
Shared draft-body lint — the code-enforced copy rules that must hold on
EVERY outbound draft, whichever inbox/transport creates it.

Two transports create Gmail drafts:
  - Inbox 1 (auto-mate.one) via the Gmail MCP `create_draft` — guarded by
    the PreToolUse hook `.claude/hooks/gmail_draft_link_guard.py`.
  - Inbox 2 (gethaytham.com) via `audit/gmail_gethaytham.create_draft` —
    the MCP hook never sees this path.

Both import `scan()` from here so the rule is defined ONCE and can't drift
between the two paths. `scan()` returns a list of human-readable problems;
empty means the body is clean.

Rules enforced:
  1. No BARE domain or email in the body. Gmail auto-links `name.tld` or
     `a@b.com` into a `google.com/url?q=...` tracking redirect that reads as
     a spam signal in a personal email (it mangled a real Susan Koruthu
     draft). Deliberate links written with an explicit http(s):// or
     mailto: scheme are allowed and stripped before scanning; a tiny
     allowlist covers bare proof domains that are known-intended.
  2. No em-dash, ever (—, U+2014). A hard voice rule for this pipeline; an
     em-dash in the body is a tell that the copy wasn't hand-shaped.
"""
from __future__ import annotations

import re

# Bare proof domains that are deliberately used and should not trip rule 1.
# Anything written with an explicit https:// scheme is already allowed, so
# keep this minimal — it's only for domains habitually written bare.
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

EM_DASH = "—"  # —


def bare_links(text: str) -> list[str]:
    """Bare domains / emails Gmail would auto-link. Empty = clean."""
    if not text:
        return []
    # Deliberate, scheme-qualified links are fine — remove them before scanning.
    work = _SCHEME_URL.sub(" ", text)

    offenders: list[str] = []
    offenders.extend(_EMAIL.findall(work))
    # Drop emails before the domain pass so their domain half isn't double-flagged.
    work = _EMAIL.sub(" ", work)
    for m in _BARE_DOMAIN.finditer(work):
        token = m.group(0)
        if token.lower() not in ALLOWLIST:
            offenders.append(token)

    seen: set[str] = set()
    unique: list[str] = []
    for tok in offenders:
        low = tok.lower()
        if low not in seen:
            seen.add(low)
            unique.append(tok)
    return unique


def scan(text: str) -> list[str]:
    """All draft-body violations, as human-readable strings. Empty = clean."""
    problems: list[str] = []

    links = bare_links(text)
    if links:
        problems.append(
            "bare domain/email Gmail will auto-link into a google.com/url "
            f"redirect: {', '.join(links)} (refer to the site by description, "
            "or write an intended link with an explicit https:// scheme)"
        )

    if text and EM_DASH in text:
        problems.append(
            "em-dash (—) in the body — a hard voice rule for this pipeline; "
            "rewrite with a comma, period, or 'and'"
        )

    return problems
