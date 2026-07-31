"""
Content extraction from a fetched page: visible text, headings, prices,
contact emails, and dates.

_Trimmed 2026-07-31. `extract_availability` went with the audit — it existed to
make an un-buyable offer machine-visible, which was a finding, and findings are
not what this machine sells. `extract_dates` stayed and gained a caller:
`outbound.qualify.latest_activity_date` uses it to settle the active-in-30-days
floor mechanically, rather than asking a worker whether a page feels current.

Its `stale_candidate` and `blog_byline` fields went the same day, in the sweep
for audit residue. `stale_candidate` was the Pam pattern — a passed kickoff
date still showing on a page — which is a finding, and `blog_byline` existed
only to stop a publish date being read as one. Nothing had ever read either.
The launch-keyword, byline and copyright regexes went with them; the one live
caller does its own copyright check on `near`, which is why that field stays._
"""

import re
from datetime import date

from bs4 import BeautifulSoup
from dateutil import parser as dateparser

from audit.email_check import name_tokens
from audit.urls import same_site


# ---------------------------------------------------------------------------
# Visible text
# ---------------------------------------------------------------------------

_STRIP_TAGS = ["script", "style", "noscript", "svg", "iframe", "template"]


def visible_text(html: str) -> str:
    """Readable page text, whitespace-normalized, one block per element."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(_STRIP_TAGS):
        tag.decompose()
    lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in soup.get_text(separator="\n").splitlines()
    ]
    return "\n".join(line for line in lines if line)


def extract_headings(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for tag in soup.find_all(["h1", "h2", "h3"]):
        text = re.sub(r"\s+", " ", tag.get_text(separator=" ", strip=True))
        if text and text not in out and "cookie" not in text.lower():
            out.append(text)
    return out[:20]


# ---------------------------------------------------------------------------
# Prices
# ---------------------------------------------------------------------------

_PRICE_RE = re.compile(
    r"(?:[$£€]\s?\d[\d,]*(?:\.\d{2})?|(?:USD|AED|GBP|EUR)\s?\d[\d,]*(?:\.\d{2})?|\d[\d,]*\s?(?:AED|USD))",
)


def extract_prices(text: str) -> list[dict]:
    """Every price-looking string with ~60 chars of surrounding context."""
    found: list[dict] = []
    seen: set[str] = set()
    for m in _PRICE_RE.finditer(text):
        price = m.group().strip()
        ctx = text[max(0, m.start() - 60): m.end() + 60].replace("\n", " ").strip()
        key = price + "|" + ctx[:40]
        if key in seen:
            continue
        seen.add(key)
        found.append({"price": price, "context": ctx})
    return found[:25]


# ---------------------------------------------------------------------------
# Contact emails
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_GENERIC_PREFIXES = {
    "info", "contact", "hello", "hi", "support", "admin", "team",
    "help", "office", "mail", "enquiries", "inquiries", "no-reply", "noreply",
    "reception", "bookings", "booking", "press", "sales", "studio",
    "newsletter", "media", "billing", "accounts", "orders",
}
_JUNK_DOMAIN_RE = re.compile(r"\.(png|jpe?g|gif|webp|svg|css|js)$", re.I)
# Platform-owned support addresses are not the lead's contact
_JUNK_HOSTS = (
    "example.com", "sentry.io", "wixpress.com", "domain.com", "email.com",
    "stanwith.me", "stan.store", "linktr.ee", "linktree.com", "beacons.ai",
    "kajabi.com", "squarespace.com", "wix.com", "godaddy.com",
)


def extract_emails(html: str, source_url: str = "", seed_url: str = "",
                   lead_name: str = "") -> dict:
    """
    Harvest emails from mailto: links and raw page text.

    Scope rule: an address only counts when the page it was found on is the
    lead's own site, OR the address's domain matches the lead's domain.
    (A radio station's reception@ address harvested from a press link is
    not her contact — that exact failure shipped once.)

    Ranking: locals containing the lead's first/last name outrank other
    personal-looking locals; generic prefixes (info@, hello@, reception@...)
    go in the generic bucket.
    """
    on_lead_site = not seed_url or same_site(source_url or seed_url, seed_url)

    # JSON-escaped markup (> etc.) otherwise glues onto addresses
    html = re.sub(r"\\u[0-9a-fA-F]{4}", " ", html)
    soup = BeautifulSoup(html, "html.parser")
    candidates: set[str] = set()

    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        if href.lower().startswith("mailto:"):
            addr = href[7:].split("?")[0].strip()
            if addr:
                candidates.add(addr.lower())

    for m in _EMAIL_RE.finditer(html):
        candidates.add(m.group().lower())

    tokens = name_tokens(lead_name, min_len=3)

    personal, generic = [], []
    for addr in sorted(candidates):
        local, _, domain = addr.partition("@")
        if _JUNK_DOMAIN_RE.search(domain) or domain in _JUNK_HOSTS:
            continue
        if "." not in domain:
            continue
        # Scope: skip addresses that belong to neither the lead's page nor
        # the lead's domain.
        if not on_lead_site and not (seed_url and same_site("https://" + domain, seed_url)):
            continue
        entry = {"email": addr, "source": source_url}
        if local in _GENERIC_PREFIXES:
            generic.append(entry)
        else:
            entry["name_match"] = any(t in local for t in tokens)
            personal.append(entry)

    personal.sort(key=lambda e: not e.get("name_match"))
    return {"personal": personal, "generic": generic}


# ---------------------------------------------------------------------------
# Dates
# ---------------------------------------------------------------------------

_DATE_PATTERNS = [
    # January 5, 2026 / Jan 5 2026 / January 5th
    re.compile(
        r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?"
        r"|Aug(?:ust)?|Sep(?:t|tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
        r"\.?\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s+\d{4})?\b"
    ),
    # 5 January 2026 / 5th Jan
    re.compile(
        r"\b\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?"
        r"|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t|tember)?|Oct(?:ober)?"
        r"|Nov(?:ember)?|Dec(?:ember)?)(?:,?\s+\d{4})?\b"
    ),
    # 01/05/2026, 2026-01-05
    re.compile(r"\b\d{1,2}/\d{1,2}/\d{4}\b"),
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
]


def extract_dates(text: str, today: date | None = None, page_url: str = "") -> list[dict]:
    """
    All parseable dates found in the text, each with its surrounding context.
    Dates written without a year get year_assumed=True — judge those
    with a human eye (could mean next year).

    `page_url` is kept in the signature because callers pass it positionally
    and it costs nothing; it no longer changes the result.
    """
    today = today or date.today()
    results: list[dict] = []
    seen: set[str] = set()

    for pattern in _DATE_PATTERNS:
        for m in pattern.finditer(text):
            raw = m.group().strip()
            ctx = text[max(0, m.start() - 80): m.end() + 80].replace("\n", " ").strip()
            near = text[max(0, m.start() - 30): m.end() + 10]
            key = raw + "|" + ctx[:40]
            if key in seen:
                continue
            seen.add(key)

            cleaned = re.sub(r"(\d)(st|nd|rd|th)\b", r"\1", raw)
            year_assumed = not re.search(r"\d{4}", raw)
            # `dayfirst` on the slash form. dateutil defaults to MONTH-first, so
            # a UAE/UK-format "03/07/2026" silently became 7 March instead of
            # 3 July — and `check_active` is a floor where a `no` is the only
            # thing that kills. An active coach was dropped with an evidence
            # string that read authoritatively. Ambiguous either way, so it is
            # resolved toward this market's convention rather than the library's.
            slash_form = "/" in cleaned
            try:
                parsed = dateparser.parse(
                    cleaned,
                    default=dateparser.parse(f"{today.year}-06-15"),
                    dayfirst=slash_form,
                ).date()
            except (ValueError, OverflowError, TypeError):
                continue

            # Bare years-in-past like "© 2024" parse oddly; also skip absurd ranges
            if parsed.year < today.year - 2 or parsed.year > today.year + 3:
                continue

            days_past = (today - parsed).days
            results.append({
                "raw": raw,
                "parsed": parsed.isoformat(),
                "days_past": days_past,
                "year_assumed": year_assumed,
                "context": ctx,
                # The tight window the copyright and byline tests actually ran
                # against. `context` is ±80 chars, so a caller re-testing for a
                # "©" in it condemns every date on a page with a footer — which
                # is every page. Callers that need "is THIS date a copyright
                # line" want `near`, not `context`.
                "near": near.replace("\n", " ").strip(),
            })

    # Closest to today FIRST, then truncate. The original order put every stale
    # candidate ahead of every fresh one — and a stale candidate required
    # days_past > 7, so a genuinely recent date always sorted after them. An
    # events archive with thirty past cohorts pushed "Posted 28 July 2026" off
    # the end of the 30, and the activity floor then read the oldest date on
    # the page as the newest. The stale flag is gone; this ordering is the part
    # that mattered and it stays.
    results.sort(key=lambda d: abs(d["days_past"]))
    return results[:30]
