"""
Content extraction from crawled pages: visible text, headings, prices,
contact emails, and stale/past dates near launch-implying copy.
"""

import re
from datetime import date, timedelta

from bs4 import BeautifulSoup
from dateutil import parser as dateparser


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
}
_JUNK_DOMAIN_RE = re.compile(r"\.(png|jpe?g|gif|webp|svg|css|js)$", re.I)
# Platform-owned support addresses are not the lead's contact
_JUNK_HOSTS = (
    "example.com", "sentry.io", "wixpress.com", "domain.com", "email.com",
    "stanwith.me", "stan.store", "linktr.ee", "linktree.com", "beacons.ai",
    "kajabi.com", "squarespace.com", "wix.com",
)


def extract_emails(html: str, source_url: str = "") -> dict:
    """
    Harvest emails from mailto: links and raw page text.
    Split into personal vs generic (info@/contact@/... prefixes).
    """
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

    personal, generic = [], []
    for addr in sorted(candidates):
        local, _, domain = addr.partition("@")
        if _JUNK_DOMAIN_RE.search(domain) or domain in _JUNK_HOSTS:
            continue
        if "." not in domain:
            continue
        entry = {"email": addr, "source": source_url}
        if local in _GENERIC_PREFIXES:
            generic.append(entry)
        else:
            personal.append(entry)
    return {"personal": personal, "generic": generic}


# ---------------------------------------------------------------------------
# Stale dates (the Pam pattern: a passed kickoff date still showing)
# ---------------------------------------------------------------------------

_LAUNCH_KEYWORDS = re.compile(
    r"start|begin|kick[\s-]?off|enroll|doors|join|goes? live|cohort|round"
    r"|register|early bird|deadline|closes?|opens?|workshop|webinar"
    r"|masterclass|challenge|event|next session|book",
    re.I,
)

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

_COPYRIGHT_RE = re.compile(r"(?:©|&copy;|copyright)", re.I)


def extract_dates(text: str, today: date | None = None) -> list[dict]:
    """
    All parseable dates found in the text, each with context and a
    stale_candidate flag: date is >7 days past AND sits near
    launch-implying copy AND is not a copyright line.
    Dates written without a year get year_assumed=True — judge those
    with a human eye (could mean next year).
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
            try:
                parsed = dateparser.parse(cleaned, default=dateparser.parse(f"{today.year}-06-15")).date()
            except (ValueError, OverflowError):
                continue

            # Bare years-in-past like "© 2024" parse oddly; also skip absurd ranges
            if parsed.year < today.year - 2 or parsed.year > today.year + 3:
                continue

            days_past = (today - parsed).days
            stale = (
                days_past > 7
                and days_past < 400
                and bool(_LAUNCH_KEYWORDS.search(ctx))
                and not _COPYRIGHT_RE.search(near)
            )
            results.append({
                "raw": raw,
                "parsed": parsed.isoformat(),
                "days_past": days_past,
                "year_assumed": year_assumed,
                "context": ctx,
                "stale_candidate": stale,
            })

    # Stale candidates first, then most recent
    results.sort(key=lambda d: (not d["stale_candidate"], abs(d["days_past"])))
    return results[:30]
