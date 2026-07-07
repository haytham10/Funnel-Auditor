"""
Content extraction from crawled pages: visible text, headings, prices,
contact emails, stale/past dates near launch-implying copy, and offer
availability (coming soon / sold out / fully booked / placeholder text).
"""

import re
from datetime import date

from bs4 import BeautifulSoup
from dateutil import parser as dateparser

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

    name_tokens = [t for t in re.split(r"[^a-z]+", lead_name.lower()) if len(t) >= 3]

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
            entry["name_match"] = any(t in local for t in name_tokens)
            personal.append(entry)

    personal.sort(key=lambda e: not e.get("name_match"))
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

# A date sitting next to a blog byline / article listing is a publish date,
# not a launch date. A quiet blog is a soft signal, not the Pam pattern.
_BYLINE_RE = re.compile(
    r"read more|min read|posted|published|blog|article|episode",
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


def extract_dates(text: str, today: date | None = None, page_url: str = "") -> list[dict]:
    """
    All parseable dates found in the text, each with context and a
    stale_candidate flag: date is >7 days past AND sits near
    launch-implying copy AND is not a copyright line or a blog byline.
    Blog publish dates get blog_byline=True and never become stale
    candidates — a quiet blog is reported separately as a soft signal.
    Dates written without a year get year_assumed=True — judge those
    with a human eye (could mean next year).
    """
    today = today or date.today()
    on_blog_page = bool(re.search(r"/(blog|news|articles|podcast)(/|$)", page_url, re.I))
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
            blog_byline = on_blog_page or bool(_BYLINE_RE.search(near))
            stale = (
                days_past > 7
                and days_past < 400
                and bool(_LAUNCH_KEYWORDS.search(ctx))
                and not _COPYRIGHT_RE.search(near)
                and not blog_byline
            )
            results.append({
                "raw": raw,
                "parsed": parsed.isoformat(),
                "days_past": days_past,
                "year_assumed": year_assumed,
                "blog_byline": blog_byline,
                "context": ctx,
                "stale_candidate": stale,
            })

    # Stale candidates first, then most recent
    results.sort(key=lambda d: (not d["stale_candidate"], abs(d["days_past"])))
    return results[:30]


# ---------------------------------------------------------------------------
# Offer availability (the empty-shelf pattern)
# ---------------------------------------------------------------------------
# The strongest finding in a July 2026 batch — a flagship course marked
# "temporarily unavailable while it gets a refresh," with six more courses
# at "coming soon" — was invisible to every existing check. Same batch:
# a "Fully Booked — no slots available" popup and a terms page shipped with
# a literal "[Insert Email]" placeholder. This extraction exists so an
# offer that cannot currently be bought is machine-visible.

_AVAILABILITY_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("coming_soon", re.compile(r"\bcoming soon\b", re.I)),
    ("unavailable", re.compile(
        r"\b(?:temporarily |currently )?unavailable\b|\bcheck back soon\b", re.I)),
    ("sold_out", re.compile(r"\bsold out\b|\bno longer available\b", re.I)),
    ("fully_booked", re.compile(
        r"\bfully booked\b|\bno slots? available\b|\bat (?:full )?capacity\b"
        r"|\bnot (?:currently )?(?:accepting|taking) (?:new )?(?:clients|bookings)\b", re.I)),
    ("closed", re.compile(
        r"\b(?:enrollment|enrolment|doors|cart|registration) (?:is |are )?closed\b", re.I)),
    ("waitlist_only", re.compile(r"\bjoin the wait\s?list\b|\bwaitlist\b", re.I)),
    ("placeholder", re.compile(r"\[(?:insert|add|your|todo)[^\]\n]{0,40}\]", re.I)),
]


def extract_availability(text: str) -> list[dict]:
    """Availability blockers with context. `waitlist_only` is only meaningful
    when it's the ONLY path to an offer — the evidence layer judges that;
    here every hit is reported with its surroundings."""
    found: list[dict] = []
    seen: set[str] = set()
    for kind, pattern in _AVAILABILITY_PATTERNS:
        for m in pattern.finditer(text):
            ctx = text[max(0, m.start() - 100): m.end() + 100].replace("\n", " ").strip()
            key = kind + "|" + ctx[:50]
            if key in seen:
                continue
            seen.add(key)
            found.append({"kind": kind, "match": m.group().strip(), "context": ctx})
    return found[:15]
