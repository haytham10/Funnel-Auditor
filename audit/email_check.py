"""
Pre-send email address check — syntax, DNS deliverability, and quality
flags, as a quotable gate line (same trust model as the other gates).

Exists because guessed addresses are a bounce risk the ramp can't afford:
one real Touch 1 went out to two guessed spellings of the same lead's
domain three minutes apart. A FAIL here means don't send to this address;
a WARN means send only with eyes open (generic inbox, unverifiable MX).

Checks, cheapest first:
  1. Syntax (RFC-shaped local@domain).
  2. Known-typo domains (gmial.com → gmail.com) — always FAIL, the fix is
     the suggestion.
  3. Disposable-mail domains — FAIL, nobody runs a coaching business on
     mailinator.
  4. DNS: MX records for the domain (falls back to an A/AAAA record, which
     RFC 5321 says can accept mail). Resolution order: dnspython if
     installed, else the system `nslookup`, else socket A-record only.
     No DNS path available → WARN inconclusive, with
     `python main.py apify verify-email <addr>` named as the fallback verifier.
  5. Role-account local part (info@, hello@, ...) → WARN, mirrors the
     Email OS rule (generic only if nothing better).
  6. --name match: local part contains a token of the lead's name → noted
     on the PASS line (personal addresses outrank).

Output contract (one line, quoted verbatim by the skills):
  EMAIL CHECK: PASS — jane@janedoe.com: MX ok (aspmx.l.google.com), personal, matches lead name
  EMAIL CHECK: WARN — info@site.com: MX ok, role account (info@) — use only if nothing better
  EMAIL CHECK: FAIL — jane@gmial.com: typo domain — did you mean jane@gmail.com?
"""

from __future__ import annotations

import re
import shutil
import socket
import subprocess
import unicodedata

_SYNTAX_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def looks_like_email(address: str) -> bool:
    """Syntax only — no DNS, no network, no judgement about deliverability.

    Split out from `check_email` so a caller that just needs "is this the shape
    of an address" does not have to run the full gate or reach into a private
    regex. `outbound.export.check_address` uses it on the last line before a row
    becomes a send.
    """
    return bool(_SYNTAX_RE.match((address or "").strip()))


def name_tokens(name: str, min_len: int = 1) -> list[str]:
    """Lowercase ASCII name tokens, accents folded (José → jose), split on any
    non-letter. `min_len` gates token length: the name-match heuristics use 3
    (skip initials that would false-match); candidate-address generation uses 1
    (a two-letter first name is still a real local part). The one shared
    tokenizer — used here, in extract.py's harvest, and in email_enrich."""
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    return [t for t in re.split(r"[^a-z]+", ascii_name.lower()) if len(t) >= min_len]

_ROLE_LOCALS = {
    "info", "contact", "hello", "hi", "support", "admin", "team", "help",
    "office", "mail", "enquiries", "inquiries", "reception", "bookings",
    "booking", "press", "sales", "studio", "newsletter", "media", "billing",
    "accounts", "orders",
}

_NEVER_SEND_LOCALS = {"no-reply", "noreply", "donotreply", "mailer-daemon", "postmaster", "abuse"}

_TYPO_DOMAINS = {
    "gmial.com": "gmail.com", "gamil.com": "gmail.com", "gmai.com": "gmail.com",
    "gmail.co": "gmail.com", "gmaill.com": "gmail.com", "googlemail.co": "googlemail.com",
    "hotmial.com": "hotmail.com", "hotmal.com": "hotmail.com", "hotmail.co": "hotmail.com",
    "outlok.com": "outlook.com", "outloook.com": "outlook.com",
    "yaho.com": "yahoo.com", "yahooo.com": "yahoo.com", "yahoo.co": "yahoo.com",
    "iclod.com": "icloud.com", "icloud.co": "icloud.com",
}

_DISPOSABLE_DOMAINS = {
    "mailinator.com", "guerrillamail.com", "10minutemail.com", "tempmail.com",
    "temp-mail.org", "throwawaymail.com", "yopmail.com", "getnada.com",
    "trashmail.com", "sharklasers.com", "dispostable.com", "maildrop.cc",
}


def _mx_via_dnspython(domain: str) -> tuple[str, list[str]] | None:
    """Returns (method, hosts) or None if dnspython isn't installed."""
    try:
        import dns.resolver  # type: ignore
    except ImportError:
        return None
    try:
        answers = dns.resolver.resolve(domain, "MX", lifetime=8)
        hosts = sorted(str(r.exchange).rstrip(".") for r in answers)
        return ("MX", hosts)
    except dns.resolver.NXDOMAIN:
        return ("NXDOMAIN", [])
    except Exception:
        # No MX is not final — RFC 5321 falls back to A/AAAA.
        try:
            dns.resolver.resolve(domain, "A", lifetime=8)
            return ("A-fallback", [domain])
        except Exception:
            return ("none", [])


def _mx_via_nslookup(domain: str) -> tuple[str, list[str]] | None:
    if not shutil.which("nslookup"):
        return None
    try:
        out = subprocess.run(
            ["nslookup", "-type=mx", domain],
            capture_output=True, text=True, timeout=10,
        ).stdout
    except Exception:
        return None
    hosts = re.findall(r"mail exchanger\s*=\s*\d+\s+(\S+)", out)
    if hosts:
        return ("MX", sorted(h.rstrip(".") for h in hosts))
    if "NXDOMAIN" in out or "can't find" in out.lower():
        # Distinguish "domain gone" from "domain fine, no MX" via A record.
        try:
            socket.getaddrinfo(domain, None)
            return ("A-fallback", [domain])
        except OSError:
            return ("NXDOMAIN", [])
    return ("none", [])


def _mx_via_socket(domain: str) -> tuple[str, list[str]]:
    """Last resort: A-record existence only — can't see MX at all."""
    try:
        socket.getaddrinfo(domain, None)
        return ("A-only", [domain])
    except OSError:
        return ("NXDOMAIN", [])


def check_email(address: str, lead_name: str = "") -> tuple[str, list[str]]:
    """Returns (verdict, details): verdict is PASS | WARN | FAIL."""
    address = address.strip()
    details: list[str] = []

    if not _SYNTAX_RE.match(address):
        return "FAIL", [f'"{address}" is not a valid address shape']

    local, _, domain = address.lower().rpartition("@")

    if local in _NEVER_SEND_LOCALS:
        return "FAIL", [f"{local}@ is a no-reply/system inbox — nothing human reads it"]

    if domain in _TYPO_DOMAINS:
        return "FAIL", [f"typo domain — did you mean {local}@{_TYPO_DOMAINS[domain]}?"]

    if domain in _DISPOSABLE_DOMAINS:
        return "FAIL", [f"{domain} is a disposable-mail domain"]

    dns_result = _mx_via_dnspython(domain) or _mx_via_nslookup(domain) or _mx_via_socket(domain)
    method, hosts = dns_result

    verdict = "PASS"
    if method == "NXDOMAIN":
        return "FAIL", [f"domain {domain} does not resolve — this address cannot receive mail"]
    if method == "MX":
        details.append(f"MX ok ({hosts[0]}" + (f" +{len(hosts) - 1}" if len(hosts) > 1 else "") + ")")
    elif method == "A-fallback":
        details.append("no MX record, but the domain resolves (RFC 5321 A-record fallback) — "
                       "deliverable in principle, soft signal")
        verdict = "WARN"
    elif method == "A-only":
        details.append("domain resolves; MX not checkable from this machine — "
                       "verify via `python main.py apify verify-email <addr>` before Touch 1")
        verdict = "WARN"
    else:
        details.append(f"domain {domain} resolves but shows no mail setup — "
                       "verify via `python main.py apify verify-email <addr>` before sending")
        verdict = "WARN"

    if local in _ROLE_LOCALS:
        details.append(f"role account ({local}@) — use only if nothing better (Email OS rule)")
        verdict = "WARN" if verdict == "PASS" else verdict
    else:
        details.append("personal")
        tokens = name_tokens(lead_name, min_len=3)
        if tokens and any(t in local for t in tokens):
            details.append("matches lead name")

    return verdict, details


def print_check(address: str, lead_name: str = "") -> int:
    verdict, details = check_email(address, lead_name)
    print(f"EMAIL CHECK: {verdict} — {address}: " + ", ".join(details))
    return 1 if verdict == "FAIL" else 0


# --- Deliverability verification (MillionVerifier result → gate verdict) -----
#
# `check_email` above is syntax + MX only. It PASSED for two addresses that
# then hard-bounced at Touch 1 (550 5.1.1 "address not found"), which is the
# whole reason this second layer exists: a bounce burns the one shared domain.
# `classify_verification` turns one `apify verify-email` result row into a
# quotable PASS/WARN/FAIL line, same trust model as everything else here —
# a script owns the verdict so it can't be talked past.
#
# The rule the skills follow: the Airtable `Email Status` field is set to `pass`
# ONLY on a literal `EMAIL VERIFY: PASS`. WARN and FAIL never auto-check it.
# So the classifier fails SAFE — anything not provably deliverable is WARN,
# never silently promoted to PASS.

# Result vocabulary → what it means for sending. The live provider is
# michael.g/email-verifier-validator via Apify; the older MillionVerifier and
# ZeroBounce tokens are kept because they overlap almost entirely and a
# retired token costs nothing, where an unlisted one drops into the
# "unrecognized" fail-safe WARN bucket and looks like a real signal. Where
# spellings differ (catch_all vs catch-all) both are listed rather than
# normalized, for the same reason.
_VERIFY_DELIVERABLE = {"ok", "valid", "deliverable"}
_VERIFY_UNDELIVERABLE = {
    "invalid": "mailbox does not exist — this is the hard-bounce case, never send here",
    "disposable": "disposable-mail domain — not a real inbox",
    "disabled": "mailbox is disabled — mail will bounce",
    "spamtrap": "known spam trap — sending here damages the domain",
    "abuse": "flagged abuse/complainer address — do not send",
    "do_not_mail": "flagged do-not-mail (role/complainer/toxic) — sending here risks "
                   "a complaint or deliverability hit, never send",
}
_VERIFY_INCONCLUSIVE = {
    "catch_all": "domain accepts all addresses, so this specific mailbox can't be "
                 "confirmed — a real bounce risk; Haytham's call before send",
    "catchall": "domain accepts all addresses, so this specific mailbox can't be "
                "confirmed — a real bounce risk; Haytham's call before send",
    "catch-all": "domain accepts all addresses, so this specific mailbox can't be "
                 "confirmed — a real bounce risk; Haytham's call before send",
    "unknown": "verifier could not determine deliverability — inconclusive, "
               "not a confirmed-good address",
    "error": "verifier errored on this address — inconclusive, try again or verify by hand",
    "no_result": "verifier was asked about this address and returned no row for it — "
                 "inconclusive, and a sign the run came back short",
    "local_mx": "local MX only, domain accepts mail, mailbox unconfirmed — "
                "no paid verifier ran, so this can never clear on its own",
}

# The tokens that mean "nothing was learned about this address", as opposed to
# "this domain accepts everything". `batch_health` reads the distinction; see
# its docstring for why it is worth keeping the two apart.
_VERIFY_NOTHING_LEARNED = frozenset({"unknown", "error", "no_result", "local_mx"})

# Below this many addresses a run of inconclusives is ordinary. Four
# catch-all domains in a row is a Tuesday; forty is an outage.
_BATCH_HEALTH_MIN = 5


def _verify_token(result: dict) -> str:
    """Pull the result token from a verify-email row, tolerating field-shape
    variance across the actor's output (result / status / resultCode)."""
    for key in ("result", "status", "resultCode", "subStatus"):
        val = result.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip().lower()
    return ""


def classify_verification(result: dict | None) -> tuple[str, list[str]]:
    """One MillionVerifier row → (verdict, details). verdict is PASS | WARN | FAIL.

    Fails SAFE: any token that is not an explicit deliverable/undeliverable
    signal (empty, missing, unrecognized, or a no-result) is WARN, so an
    ambiguous verification never checks the `Email Verified` box on its own.
    """
    if not result:
        return "WARN", ["verifier returned no result for this address — "
                        "inconclusive, cannot confirm deliverability"]

    token = _verify_token(result)
    if not token:
        return "WARN", ["verifier returned no readable result field — inconclusive"]

    if token in _VERIFY_DELIVERABLE:
        extras = []
        if result.get("role"):
            extras.append("role account")
        if result.get("free"):
            extras.append("free provider")
        tail = (" (" + ", ".join(extras) + ")") if extras else ""
        return "PASS", [f"mailbox confirmed deliverable ({token}){tail}"]

    if token in _VERIFY_UNDELIVERABLE:
        return "FAIL", [_VERIFY_UNDELIVERABLE[token]]

    if token in _VERIFY_INCONCLUSIVE:
        return "WARN", [_VERIFY_INCONCLUSIVE[token]]

    # Unrecognized token: never guess PASS.
    return "WARN", [f'unrecognized verifier result "{token}" — treated as inconclusive, '
                    "not a confirmed-good address"]


def verify_local(emails: list[str], lead_name: str = "") -> list[dict]:
    """The no-provider fallback: `check_email` per address, in the row shape
    `classify_verification` reads. One row per input, in input order.

    This is everything the machine can learn about an address without paying
    anybody — syntax, the never-send and typo and disposable lists, and the
    three-way MX ladder. What it CANNOT do is confirm a mailbox exists, because
    there is no SMTP probe here and there is not going to be one: cloud IPs are
    widely blocked on port 25, the big hosts accept-all anyway, and a probe from
    a container reads as reconnaissance to some mail hosts.

    So a domain that resolves comes back as `local_mx`, which classifies to WARN
    and says so in the details. It is a real signal — a FAIL here is a genuine
    kill, and that is most of the value — but it can never check the CRM's
    `Email Verified` box on its own, and nothing downstream should let it.

    This replaced ZeroBounce (deleted 2026-08-01), which was documented as the
    automatic fallback and, when the outage finally called on it, turned out to
    have no credits. A fallback nobody has exercised is a fallback nobody has.
    """
    rows: list[dict] = []
    for address in emails:
        address = (address or "").strip()
        verdict, details = check_email(address, lead_name)
        reason = ", ".join(details)
        if verdict != "FAIL":
            # PASS and WARN both mean the same thing here: the domain can take
            # mail and the mailbox is unconfirmed. The gap between them is MX
            # vs an A-record fallback, which is a detail, not a verdict.
            token = "local_mx"
        elif "disposable" in reason:
            token = "disposable"
        else:
            # Bad shape, a no-reply local, a typo domain, or NXDOMAIN. All of
            # them are "do not send here", which is what `invalid` means.
            token = "invalid"
        rows.append({
            "email": address,
            "status": verdict.lower(),
            "result": token,
            "reason": reason,
            "role": any("role account" in d for d in details),
            "verified_by": "local",
        })
    return rows


def batch_health(results: list[dict] | None) -> str | None:
    """One line naming a verifier outage, or None when the batch looks real.

    A dead verifier and a run of genuine catch-all domains both surface as WARN,
    one address at a time, and that is exactly how the 2026-07-31 outage went
    unnoticed for 40 leads: every address came back inconclusive and the operator
    read it as "lots of catch-all domains."

    The tell is the shape of the whole run rather than any one row. Every
    address in a batch coming back inconclusive is not an address pattern —
    real lists are mixed. So: at `_BATCH_HEALTH_MIN` addresses or more, either
    nothing conclusive at all, or 90%+ of rows saying nothing was learned, is
    reported as SUSPECT.

    Deliberately NOT a per-address verdict. Nothing is wrong with the addresses,
    so no address should be marked bad; what is wrong is the run, which is why
    the caller exits 2 (the gate could not complete) rather than 1.
    """
    rows = [r for r in (results or []) if isinstance(r, dict)]
    if len(rows) < _BATCH_HEALTH_MIN:
        return None

    # A run that was answered entirely by the local check learns nothing about
    # any mailbox BY DESIGN, so the shape below is guaranteed and reporting it
    # would fire on every local run. That is the "warning nobody reads" failure,
    # and a check that always fires protects nothing. The operator already sees
    # `[via local]` on every line, plus the switch note when a quota forced it.
    if rows and all((r.get("verified_by") or "") == "local" for r in rows):
        return None

    verdicts = [classify_verification(r)[0] for r in rows]
    nothing_learned = sum(1 for r in rows if _verify_token(r) in _VERIFY_NOTHING_LEARNED)
    total = len(rows)

    if not any(v in ("PASS", "FAIL") for v in verdicts):
        return (f"EMAIL VERIFY BATCH: SUSPECT — {total}/{total} inconclusive. "
                f"No real list verifies this way; treat the verifier as down, "
                f"not the addresses as catch-alls.")
    if nothing_learned / total >= 0.9:
        return (f"EMAIL VERIFY BATCH: SUSPECT — {nothing_learned}/{total} rows "
                f"learned nothing about the address. Check the verifier before "
                f"trusting any row in this run.")
    return None


def print_verify(address: str, result: dict | None, *, note: str = "") -> int:
    """Format one verification result as the quotable gate line. `note`
    (e.g. "Apify at 92% of its monthly cap — auto-switched to the local check")
    folds into the same line rather than a second line, so the "quote the
    literal output line" convention still holds. Exit 1 only on FAIL
    (unusable address); PASS and WARN exit 0, mirroring email-check.

    The line names who answered. Two WARNs that read identically but came from
    a paid verifier and from the local MX check are not the same fact, and
    reading them as the same fact is what the batch check above exists to stop.
    """
    verdict, details = classify_verification(result)
    by = (result or {}).get("verified_by") or "none"
    # The local check knows WHY, where the classifier only knows the token —
    # but the two are useful in opposite directions. On a FAIL the classifier's
    # canned line can be wrong ("mailbox does not exist" is false of a domain
    # that never resolved), so the local reason replaces it. On a WARN the
    # canned line IS the point ("mailbox unconfirmed"), and the local detail
    # would read like a pass on its own, so it goes after rather than instead.
    own_reason = (result or {}).get("reason") if by == "local" else ""
    if own_reason:
        details = [own_reason] if verdict == "FAIL" else list(details) + [own_reason]
    line = f"EMAIL VERIFY: {verdict} — {address}: " + ", ".join(details)
    line += f" [via {by}]"
    if note:
        line += f" [{note}]"
    print(line)
    return 1 if verdict == "FAIL" else 0
