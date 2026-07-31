"""The fetch ladder: free first, Apify only for what free can't read.

Firecrawl is gone. What replaces it is not one tool but an order of preference,
because the measured cost of the old pipeline was dominated by a rendering mode
nobody chose on purpose.

    tier 0   local requests + BeautifulSoup            free
    tier 1   the agent's own WebSearch/WebFetch        free, model-side
    tier 2   ONE batched Apify cheerio run             paid, shared

Three findings from the last cost audit shape this module:

1. **Container boot dominates the bill, not pages.** A 2-page run and a 200-page
   run cost nearly the same to start. Fifty separate 2-page runs is the worst
   possible way to use a compute-billed actor, so tier 2 never fires per lead.
   It fires once per batch, over every URL tier 0 failed on, via
   `apify_batch_plan`.

2. **The crawler's rendering mode is a trap.** Called over the API without
   setting `crawlerType`, the actor defaults to full headless Firefox, the most
   expensive mode there is. One test run spent 81 seconds on 2 pages and 45% of
   that lead's entire bill. The plan this module builds always sets `cheerio`
   explicitly, and only names `playwright:adaptive` for a URL that came back
   empty from a real HTTP fetch.

3. **Crawl depth misses the pages that matter.** Depth-2 from a homepage missed
   `/about.html` entirely on a real lead. So candidate URLs are enumerated
   directly rather than discovered: this module guesses the standard paths and
   passes them all in one `startUrls` array.

Most coach sites are static marketing pages. Tier 0 should carry the large
majority of them; instrument `batch_fetch`'s report to find out for your list
rather than trusting that sentence.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from audit.extract import visible_text, extract_headings, extract_emails, extract_prices
from audit.urls import normalize as normalize_url, same_site

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
TIMEOUT = 15
MIN_USEFUL_TEXT = 200          # below this a page is a shell, escalate it

# The paths worth trying on a coach site, in the order they pay off. About and
# contact carry the identity and the address; work/services and pricing carry
# the offer and the number.
CANDIDATE_PATHS = (
    "", "/about", "/about-us", "/about-me", "/contact", "/contact-us",
    "/work-with-me", "/services", "/coaching", "/programs", "/pricing",
)


@dataclass
class Page:
    url: str
    status: int = 0
    html: str = ""
    text: str = ""
    error: str = ""

    @property
    def ok(self) -> bool:
        return self.status == 200 and len(self.text) >= MIN_USEFUL_TEXT

    @property
    def thin(self) -> bool:
        """Fetched fine but came back empty — the signature of a JS-rendered
        page, and the only honest reason to escalate to a browser."""
        return self.status == 200 and len(self.text) < MIN_USEFUL_TEXT


@dataclass
class SiteRead:
    """Everything tier 0 got from one lead's site."""
    domain: str = ""
    pages: list[Page] = field(default_factory=list)
    emails: list[dict] = field(default_factory=list)
    prices: list[dict] = field(default_factory=list)
    headings: list[str] = field(default_factory=list)
    social: dict[str, str] = field(default_factory=dict)
    escalate: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return any(page.ok for page in self.pages)

    @property
    def text(self) -> str:
        return "\n\n".join(page.text for page in self.pages if page.ok)


_SOCIAL_RE = {
    "linkedin": re.compile(r"https?://([a-z]{2,3}\.)?linkedin\.com/(in|company)/[\w\-%.]+", re.I),
    "instagram": re.compile(r"https?://(www\.)?instagram\.com/[\w\-.]+", re.I),
    "youtube": re.compile(r"https?://(www\.)?youtube\.com/(@[\w\-.]+|channel/[\w\-]+|c/[\w\-]+)", re.I),
    "facebook": re.compile(r"https?://(www\.)?facebook\.com/[\w\-.]+", re.I),
    "tiktok": re.compile(r"https?://(www\.)?tiktok\.com/@[\w\-.]+", re.I),
}


def _session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })
    return session


def get_page(url: str, session: requests.Session | None = None) -> Page:
    """One page, free. Never raises — a failure is a Page with an error on it."""
    session = session or _session()
    try:
        response = session.get(url, timeout=TIMEOUT, allow_redirects=True)
    except requests.RequestException as exc:
        return Page(url=url, error=type(exc).__name__)

    content_type = response.headers.get("content-type", "")
    if "html" not in content_type.lower():
        return Page(url=url, status=response.status_code,
                    error=f"not html ({content_type.split(';')[0]})")

    html = response.text
    return Page(url=url, status=response.status_code, html=html,
                text=visible_text(html))


def discover_paths(homepage_html: str, base_url: str, limit: int = 6) -> list[str]:
    """Same-site links whose text or href suggests about/contact/pricing.

    Cheaper and more reliable than crawling: we already have the homepage, and
    its nav names the pages that matter.
    """
    wanted = re.compile(
        r"about|contact|work[-\s]?with|service|coach|program|pricing|invest|hire",
        re.I,
    )
    found: list[str] = []
    soup = BeautifulSoup(homepage_html, "html.parser")
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if href.startswith(("mailto:", "tel:", "#", "javascript:")):
            continue
        absolute = normalize_url(urljoin(base_url, href))
        if not same_site(absolute, base_url) or absolute in found or absolute == base_url:
            continue
        label = " ".join([anchor.get_text(" ", strip=True) or "", href])
        if wanted.search(label):
            found.append(absolute)
        if len(found) >= limit:
            break
    return found


def read_site(site_url: str, *, max_pages: int = 5,
              session: requests.Session | None = None,
              pause: float = 0.3) -> SiteRead:
    """Tier 0 for one lead. Homepage, then whatever its nav points at.

    Enumerates candidate paths rather than trusting crawl depth — the failure
    that lost `/about.html` on a real lead was a depth limit, not a bad URL.
    """
    session = session or _session()
    read = SiteRead(domain=urlparse(site_url).netloc)

    home = get_page(site_url, session)
    read.pages.append(home)
    if home.thin:
        read.escalate.append(home.url)
    if not home.html:
        read.notes.append(f"homepage unreachable: {home.error or home.status}")
        return read

    targets = discover_paths(home.html, site_url, limit=max_pages - 1)
    if not targets:
        # No usable nav. Fall back to guessing the standard paths.
        targets = [normalize_url(urljoin(site_url, p))
                   for p in CANDIDATE_PATHS[1:max_pages]]
        read.notes.append("no nav links matched, guessed standard paths")

    for url in targets[: max_pages - 1]:
        time.sleep(pause)
        page = get_page(url, session)
        if page.status == 404:
            continue
        read.pages.append(page)
        if page.thin:
            read.escalate.append(page.url)

    _harvest(read, site_url)
    return read


def _harvest(read: SiteRead, seed_url: str) -> None:
    """Pull the structured data out of whatever pages came back."""
    # `extract_emails` returns {"personal": [...], "generic": [...]}, and
    # `list.extend(dict)` iterates the KEYS — so this used to fill read.emails
    # with the strings "personal" and "generic" and then crash on `.get`. It
    # crashed on the first page of the first real site, which is how long the
    # tier-0 path went without ever being run against one.
    #
    # The two buckets are kept apart until the end so a jane@ on page four
    # still outranks an info@ on page one. Ranking by page order would hand the
    # batch a mailbox nobody reads.
    personal: list[dict] = []
    generic: list[dict] = []
    for page in read.pages:
        if not page.html:
            continue
        found = extract_emails(page.html, source_url=page.url, seed_url=seed_url)
        personal.extend(found.get("personal", []))
        generic.extend(found.get("generic", []))
        read.headings.extend(extract_headings(page.html))
        read.prices.extend(extract_prices(page.text))
        for platform, pattern in _SOCIAL_RE.items():
            if platform in read.social:
                continue
            match = pattern.search(page.html)
            if match:
                read.social[platform] = normalize_url(match.group(0))

    seen: set[str] = set()
    deduped = []
    for entry in personal + generic:
        address = (entry.get("email") or "").lower()
        if address and address not in seen:
            seen.add(address)
            deduped.append(entry)
    read.emails = deduped
    read.headings = list(dict.fromkeys(read.headings))[:40]


# ------------------------------------------------------------- tier 2 planning


APIFY_SITE_CRAWLER = "apify/website-content-crawler"


def apify_batch_plan(urls: list[str], *, render: bool = False,
                     max_pages_per_start: int = 1) -> dict:
    """Build ONE actor input for every URL tier 0 failed on, across the batch.

    This is the cost lever. Passing fifty leads' URLs in a single `startUrls`
    array pays one container boot instead of fifty. `crawlerType` is always set
    explicitly, because leaving it unset is what silently bought full headless
    Firefox on the run that cost 6x its estimate.

    `render=True` is only correct for URLs that returned 200 with no text —
    a genuinely JS-rendered page. Never set it as a default for a batch.
    """
    return {
        "actor": APIFY_SITE_CRAWLER,
        "input": {
            "startUrls": [{"url": url} for url in dict.fromkeys(urls)],
            "crawlerType": "playwright:adaptive" if render else "cheerio",
            "maxCrawlDepth": 0,
            "maxCrawlPages": max(1, len(urls) * max_pages_per_start),
            "saveHtml": True,
            "saveMarkdown": False,
            "proxyConfiguration": {"useApifyProxy": True},
        },
        "why": (
            f"{len(urls)} URL(s) in one run: one container boot, "
            f"{'browser render (thin pages only)' if render else 'cheerio (static HTML)'}"
        ),
    }


def _read_key(lead) -> str:
    """A key that is unique per LEAD, not per name.

    `slug` comes from the name and falls back to the domain, so two rows from a
    directory that share a company site — or two coaches with the same name —
    collapsed into one entry. `partition` dedupes on name and email but never on
    domain, so nameless rows survive to here. The survivor's page text is then
    the other person's, and it feeds qualify and the hook.
    """
    return (getattr(lead, "email", "") or "").strip().lower() or \
        f"{getattr(lead, 'slug', '')}|{getattr(lead, 'site_url', '')}"


def batch_fetch(leads: list, *, max_pages: int = 5) -> dict:
    """Tier 0 across a whole batch, then the plan for what it couldn't read.

    Returns the per-lead reads plus a single Apify plan for the failures, so
    the caller pays for at most one actor run no matter how big the batch.
    """
    session = _session()
    reads: dict[str, SiteRead] = {}
    dead: list[str] = []
    thin: list[str] = []

    for lead in leads:
        if not getattr(lead, "site_url", ""):
            continue
        read = read_site(lead.site_url, max_pages=max_pages, session=session)
        reads[_read_key(lead)] = read
        if read.escalate:
            thin.extend(read.escalate)
        elif not read.ok:
            dead.append(lead.site_url)

    plans = []
    if dead:
        plans.append(apify_batch_plan(dead, render=False))
    if thin:
        plans.append(apify_batch_plan(thin, render=True))

    attempted = len(reads)
    return {
        "reads": reads,
        "ok": sum(1 for r in reads.values() if r.ok),
        "attempted": attempted,
        "tier0_rate": round(sum(1 for r in reads.values() if r.ok) / attempted, 3)
        if attempted else 0.0,
        "escalate_plans": plans,
        "report": (
            f"TIER 0: {sum(1 for r in reads.values() if r.ok)}/{attempted} sites "
            f"read free. {len(dead)} unreachable, {len(thin)} thin. "
            f"{len(plans)} batched Apify run(s) needed."
        ),
    }
