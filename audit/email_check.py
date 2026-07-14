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

_SYNTAX_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

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
        tokens = [t for t in re.split(r"[^a-z]+", lead_name.lower()) if len(t) >= 3]
        if tokens and any(t in local for t in tokens):
            details.append("matches lead name")

    return verdict, details


def print_check(address: str, lead_name: str = "") -> int:
    verdict, details = check_email(address, lead_name)
    print(f"EMAIL CHECK: {verdict} — {address}: " + ", ".join(details))
    return 1 if verdict == "FAIL" else 0
