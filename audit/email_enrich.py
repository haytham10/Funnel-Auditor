"""
Nominative email enrichment — the no-email fallback stage.

When the walk harvests no address, this derives candidate addresses from the
lead's name + their OWN branded domain (jane@, jane.doe@, jdoe@, ...), verifies
them through the existing deliverability checker, and — only if exactly one
candidate comes back provably deliverable — adopts it as the lead's address.

It builds nothing new for verification: `email_verifier.verify_emails` (one
batched ZeroBounce call) and `email_check.classify_verification` (the
fail-safe PASS/WARN/FAIL verdict) do that work. This module owns only
candidate GENERATION plus the convergence rules that keep guessing safe.

Three safety properties, non-negotiable — the reason `email_check`'s header
exists ("one real Touch 1 went out to two guessed spellings of the same lead's
domain three minutes apart"):

  1. Converge on exactly ONE address. All candidates are verified in one call;
     among the PASS results only the single top-ranked candidate is adopted, the
     rest are logged as `discarded`. Two guessed spellings never both go out.
  2. Never auto-PASS on a catch-all domain. A catch-all answers `catch_all`
     (→ WARN) for every guess, so no specific mailbox is confirmable —
     `classify_verification` already fails safe there, and this reports HOLD and
     adopts nothing.
  3. Refuse free-provider domains. Nominative permutation only makes sense
     against a lead's own branded domain — never guess `jane.doe@gmail.com`.

Output contract (one line, quoted verbatim by the skills — a PASS here IS an
`EMAIL VERIFY: PASS` on the adopted address, so it authorizes checking the
Notion `Email Verified` box exactly like a harvested-then-verified address):
  EMAIL ENRICH: PASS — jane@janedoe.com: guessed first@, verified deliverable
  EMAIL ENRICH: HOLD — janedoe.com: catch-all domain, 6 candidates inconclusive — no auto-send
  EMAIL ENRICH: NONE — janedoe.com: no candidate verified deliverable
  EMAIL ENRICH: NONE — gmail.com: free-provider domain, cannot nominatively guess
"""

from __future__ import annotations

from audit import email_check
from audit.urls import registrable_domain

# Consumer mailbox providers: a lead on one of these has no branded domain to
# permute against, so nominative guessing is meaningless (jane.doe@gmail.com is
# not derivable from a name). Mirrors the spirit of _DISPOSABLE_DOMAINS.
FREE_PROVIDERS = {
    "gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "live.com",
    "msn.com", "yahoo.com", "ymail.com", "icloud.com", "me.com", "mac.com",
    "aol.com", "proton.me", "protonmail.com", "gmx.com", "zoho.com",
    "mail.com", "yandex.com", "pm.me",
}


def candidate_locals(full_name: str) -> list[str]:
    """Ranked, deduped local-parts for a name — most-likely first.

    "Jane Doe" -> ["jane", "jane.doe", "janedoe", "jdoe", "jane_doe",
                   "janed", "j.doe", "doe"]
    A single-token name yields just the first name. Returns [] for an empty or
    tokenless name (nothing to guess from)."""
    tokens = email_check.name_tokens(full_name, min_len=1)
    if not tokens:
        return []

    first = tokens[0]
    if len(tokens) == 1:
        return [first]

    last = tokens[-1]
    fi, li = first[0], last[0]

    ranked = [
        first,                 # jane
        f"{first}.{last}",     # jane.doe
        f"{first}{last}",      # janedoe
        f"{fi}{last}",         # jdoe
        f"{first}_{last}",     # jane_doe
        f"{first}{li}",        # janed
        f"{fi}.{last}",        # j.doe
        last,                  # doe
    ]

    seen: set[str] = set()
    out: list[str] = []
    for local in ranked:
        if local and local not in seen:
            seen.add(local)
            out.append(local)
    return out


def enrich(full_name: str, domain_or_url: str, *, verifier=None, shape_check=None) -> dict:
    """Generate name-based candidates against the lead's domain, verify them in
    one batched call, and converge on at most one deliverable address.

    `verifier` turns a list of addresses into a list of verification result
    rows — defaults to `email_verifier.verify_emails` (ZeroBounce). `shape_check`
    is the free domain-level gate (syntax/typo/disposable/dead-domain) —
    defaults to `email_check.check_email`. Both are injectable so tests
    exercise the convergence logic without touching the network.

    Returns a dict:
      {"verdict": "PASS"|"HOLD"|"NONE",
       "address": <str|None>,      # adopted address, only on PASS
       "pattern": <str|None>,      # its local-part shape, only on PASS
       "domain":  <registrable domain>,
       "candidates": [<addr>, ...],  # what was actually verified, in rank order
       "discarded": [<addr>, ...],   # other PASS addresses NOT adopted (safety log)
       "reason":  <str>}            # human-readable one-liner for the gate line
    """
    # Tolerate an address slipping in where a domain was expected (jane@site.com
    # -> site.com); a real Site URL with no '@' is unaffected.
    domain = registrable_domain(domain_or_url.rsplit("@", 1)[-1])
    base = {"verdict": "NONE", "address": None, "pattern": None,
            "domain": domain, "candidates": [], "discarded": []}

    if not domain:
        return {**base, "reason": "no domain to guess against"}

    if domain in FREE_PROVIDERS:
        return {**base, "reason": "free-provider domain, cannot nominatively guess"}

    locals_ranked = candidate_locals(full_name)
    if not locals_ranked:
        return {**base, "reason": "no usable name tokens to build candidates from"}

    candidates = [f"{local}@{domain}" for local in locals_ranked]

    # Domain gate, once (not per candidate): generated candidates are all
    # syntactically valid by construction, and the domain is uniform — so a FAIL
    # from the free shape check (typo domain / disposable / dead domain that
    # doesn't resolve) condemns every candidate. Bail before spending a single
    # verify credit on a domain that can't receive mail at all.
    if shape_check is None:
        shape_check = email_check.check_email
    gate_verdict, gate_details = shape_check(candidates[0], full_name)
    if gate_verdict == "FAIL":
        detail = gate_details[0] if gate_details else "domain is unusable"
        return {**base, "reason": f"domain failed the shape check: {detail}"}

    base["candidates"] = candidates

    if verifier is None:
        from audit import email_verifier
        verifier = email_verifier.verify_emails

    rows = verifier(candidates) or []
    # Map each returned row back to its address so we can rank PASS results by
    # the original candidate order (verifiers may reorder or drop rows).
    by_addr = {}
    for row in rows:
        addr = (row.get("email") or "").strip().lower()
        if addr:
            by_addr[addr] = row

    passed = []
    for addr in candidates:  # candidate/rank order
        result = by_addr.get(addr.lower())
        verdict, _ = email_check.classify_verification(result)
        if verdict == "PASS":
            passed.append(addr)

    if passed:
        adopted = passed[0]
        local = adopted.partition("@")[0]
        return {**base, "verdict": "PASS", "address": adopted,
                "pattern": _pattern_label(local, full_name),
                "discarded": passed[1:],
                "reason": f"guessed {_pattern_label(local, full_name)}, verified deliverable"}

    # Nothing confirmed. Distinguish "domain swallows everything / inconclusive"
    # (HOLD — a human could still chase it) from "every candidate came back
    # undeliverable" (NONE — the domain has no matching mailbox).
    any_inconclusive = False
    for addr in candidates:
        verdict, _ = email_check.classify_verification(by_addr.get(addr.lower()))
        if verdict == "WARN":
            any_inconclusive = True
            break

    if any_inconclusive:
        return {**base, "verdict": "HOLD",
                "reason": f"catch-all or inconclusive domain, "
                          f"{len(candidates)} candidates unconfirmed — no auto-send"}

    return {**base, "reason": "no candidate verified deliverable"}


def _pattern_label(local: str, full_name: str) -> str:
    """Name the shape of a local-part for the gate line (first@, first.last@, ...)."""
    tokens = email_check.name_tokens(full_name, min_len=1)
    if len(tokens) < 2:
        return "first@"
    first, last = tokens[0], tokens[-1]
    fi, li = first[0], last[0]
    known = {
        first: "first@",
        f"{first}.{last}": "first.last@",
        f"{first}{last}": "firstlast@",
        f"{fi}{last}": "flast@",
        f"{first}_{last}": "first_last@",
        f"{first}{li}": "firstl@",
        f"{fi}.{last}": "f.last@",
        last: "last@",
    }
    return known.get(local, f"{local}@")


def print_enrich(full_name: str, domain_or_url: str, *, verifier=None, shape_check=None) -> int:
    """Run enrichment and print the one quotable gate line. Exit 1 only when
    nothing was adopted (PASS exits 0); mirrors the other email gates."""
    r = enrich(full_name, domain_or_url, verifier=verifier, shape_check=shape_check)
    subject = r["address"] if r["verdict"] == "PASS" else (r["domain"] or domain_or_url)
    line = f"EMAIL ENRICH: {r['verdict']} — {subject}: {r['reason']}"
    if r["verdict"] == "PASS" and r["discarded"]:
        line += f" (also-verified, not used: {', '.join(r['discarded'])})"
    print(line)
    return 0 if r["verdict"] == "PASS" else 1
