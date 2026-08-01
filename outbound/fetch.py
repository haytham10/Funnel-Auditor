"""The fetch ladder: free first, Apify only for what free can't read.

Firecrawl is gone. What replaces it is not one tool but an order of preference,
because the measured cost of the old pipeline was dominated by a rendering mode
nobody chose on purpose.

    tier 0   local requests + BeautifulSoup            free, concurrent
    tier 1   the agent's own WebSearch/WebFetch        free, model-side
    tier 2a  ONE batched apify/cheerio-scraper run     paid, shared, static
    tier 2b  ONE batched website-content-crawler run   paid, shared, renders

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
import threading
import time
from concurrent.futures import ThreadPoolExecutor
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
    # How long this one page took. The first per-retrieval timing in the repo —
    # `batch_fetch`'s elapsed_secs is batch-wide, and was the only clock here.
    secs: float = 0.0

    @property
    def ok(self) -> bool:
        return self.status == 200 and len(self.text) >= MIN_USEFUL_TEXT

    @property
    def outcome(self) -> str:
        """The ledger's word for how this fetch went."""
        if self.error:
            return "error"
        if self.status != 200:
            return "error"
        return "ok" if self.ok else "empty"

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
    # Does this site mention the person the row is about? confirmed | absent |
    # unknown. About 40 of 151 rows on the first batch pointed at somebody
    # else entirely — parked domains, name collisions, a coach's training
    # school, an Ohio retreat house, a Dutch tech-news site — and nothing
    # checked, so every one was found by hand after the money was spent.
    owner_match: str = "unknown"

    @property
    def ok(self) -> bool:
        return any(page.ok for page in self.pages)

    @property
    def text(self) -> str:
        return "\n\n".join(page.text for page in self.pages if page.ok)


# What a profile URL looks like, per platform. Matched against raw HTML and
# taken leftmost-first, which is the reason for the exclusions below.
#
# **A pattern that matches infrastructure harvests infrastructure.** The
# facebook and instagram patterns used to be bare `[\w\-.]+` after the host, and
# on any lead running Meta ads that returned:
#
#     facebook   -> https://facebook.com/tr     the pixel, from <head>
#     instagram  -> https://instagram.com/p     an embedded post's permalink
#
# Both beat the real profile because a pixel snippet and an embed sit in the
# head while the social bar sits in the footer, and `search` takes the first
# match. Neither is a page anybody owns, so the URL was wrong in `sites.json`,
# wrong in every worker prompt built from it, and — once ownership became typed
# — would have scored `absent` and read as a name collision rather than as a
# tracking script. Exclude the known non-profile paths rather than ranking
# matches: the list is short, it is stable, and it says what it is doing.
_SOCIAL_RE = {
    "linkedin": re.compile(r"https?://([a-z]{2,3}\.)?linkedin\.com/(in|company)/[\w\-%.]+", re.I),
    "instagram": re.compile(
        r"https?://(www\.)?instagram\.com/(?!(?:p|reel|reels|explore|tv|stories|accounts)[/?#]|(?:p|reel|reels|explore|tv|stories|accounts)$)[\w\-.]+", re.I),
    "youtube": re.compile(r"https?://(www\.)?youtube\.com/(@[\w\-.]+|channel/[\w\-]+|c/[\w\-]+)", re.I),
    "facebook": re.compile(
        r"https?://(www\.)?facebook\.com/(?!(?:tr|sharer|sharer\.php|share|share\.php|plugins|dialog|v\d+\.\d+)[/?#]|(?:tr|sharer|sharer\.php|share|share\.php|plugins|dialog)$)[\w\-.]+", re.I),
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
    started = time.monotonic()
    try:
        response = session.get(url, timeout=TIMEOUT, allow_redirects=True)
    except requests.RequestException as exc:
        return Page(url=url, error=type(exc).__name__,
                    secs=round(time.monotonic() - started, 2))

    elapsed = round(time.monotonic() - started, 2)
    content_type = response.headers.get("content-type", "")
    if "html" not in content_type.lower():
        return Page(url=url, status=response.status_code, secs=elapsed,
                    error=f"not html ({content_type.split(';')[0]})")

    html = response.text
    return Page(url=url, status=response.status_code, html=html,
                text=visible_text(html), secs=elapsed)


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


def apify_batch_plan(urls: list[str], *, render: bool = False,
                     max_pages_per_start: int = 1) -> dict:
    """Build ONE escalation for every URL tier 0 failed on, across the batch.

    This is the cost lever. Passing fifty leads' URLs in a single run pays one
    container boot instead of fifty.

    The plan names an `actor_key` from `audit.apify.ACTORS` rather than an actor
    id, which is the difference between a plan and a suggestion. It used to name
    `apify/website-content-crawler` in the slash form, which was in no ACTORS
    map — so nothing could run it through the cost gate, it was something the
    operator executed by hand outside the approval path, and the first real
    batch skipped it entirely and used free WebSearch instead.

    `render=True` is only correct for URLs that returned 200 with no text — a
    genuinely JS-rendered page. Never set it as a default for a batch: the
    browser mode is the most expensive thing this module can ask for.
    """
    targets = list(dict.fromkeys(urls))
    return {
        "actor_key": "site_render" if render else "site_static",
        "urls": targets,
        "max_pages_per_start": max_pages_per_start,
        "why": (
            f"{len(targets)} URL(s) in one run: one container boot, "
            f"{'browser render (thin pages only)' if render else 'cheerio (static HTML)'}"
        ),
    }


def run_plan(plan: dict, *, approved: bool = False) -> list[dict]:
    """Execute one escalation plan through the cost gate.

    Deliberately a thin dispatch. Everything about how each actor is called —
    the input shape, the page function, the explicit `crawlerType` — lives in
    `audit/apify.py` next to the actor it belongs to, so this module never
    grows a second, drifting copy of it.
    """
    from audit import apify

    urls = plan.get("urls") or []
    if plan.get("actor_key") == "site_render":
        return apify.crawl_render(urls, approved=approved)
    return apify.crawl_static(urls, approved=approved)


def check_owner(read: SiteRead, name: str) -> str:
    """Does this site mention the person the row says it belongs to?

    `confirmed` when a name token appears, `absent` when the site read fine and
    none does, `unknown` when there was nothing to look at or no name to look
    for. Uses the one shared tokenizer, at `min_len=3` so an initial cannot
    match everything.

    **Advisory, never a kill.** A real coach's site may carry only a brand name,
    and a false kill here is permanent and invisible. What this buys is that the
    ~40 bad rows in a 151-lead list surface in one report line before any money
    is spent, instead of one at a time, by hand, after it.
    """
    from audit.email_check import name_tokens

    tokens = name_tokens(name or "", min_len=3)
    if not tokens or not read.ok:
        return "unknown"
    haystack = " ".join(
        [read.text] + [p.url for p in read.pages] + read.headings).lower()
    return "confirmed" if any(t in haystack for t in tokens) else "absent"


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


DEFAULT_WORKERS = 8

# One session per worker thread. `requests.Session` is not thread-safe — its
# connection pool and cookie jar are shared mutable state — so the single shared
# session the serial loop used cannot simply be handed to a pool.
_local = threading.local()


def _thread_session() -> requests.Session:
    session = getattr(_local, "session", None)
    if session is None:
        session = _session()
        _local.session = session
    return session


def batch_fetch(leads: list, *, max_pages: int = 5,
                workers: int = DEFAULT_WORKERS) -> dict:
    """Tier 0 across a whole batch, then the plan for what it couldn't read.

    Returns the per-lead reads plus a single Apify plan for the failures, so
    the caller pays for at most one actor run no matter how big the batch.

    **Concurrent, because serial did not finish.** This was a plain `for` loop:
    151 sites, up to five pages each, at a 15-second timeout. It exceeded a
    120-second ceiling, then a 590-second one, and was killed twice before
    completing on the first real batch — so the whole stage had to be run in the
    background and watched. The work is entirely network-bound, which is the
    case threads are actually good at.

    Politeness is unchanged: one lead is one thread is one host, and the 0.3s
    pause between pages of a site still happens inside `read_site`. Nothing here
    makes more requests to any single host than before.

    Results are collected into a dict keyed by `_read_key`, so completion order
    does not leak into the output.
    """
    reads: dict[str, SiteRead] = {}
    dead: list[str] = []
    thin: list[str] = []
    targets = [l for l in leads if getattr(l, "site_url", "")]
    started = time.monotonic()

    # The leads this stage cannot help with, named rather than left to be
    # rediscovered. A lead with no site produced nothing at all here, so the
    # research worker met it cold and improvised — which is how the last batch
    # came to use WebSearch and Instagram without either being a rung anybody
    # had planned. Naming them turns that into handed-out work.
    needs_search, ig_only = [], []
    for lead in leads:
        if getattr(lead, "site_url", ""):
            continue
        handle = getattr(lead, "instagram_url", "")
        socials = lead.social_urls() if hasattr(lead, "social_urls") else []
        if handle and not [s for s in socials if s != handle]:
            ig_only.append({"name": getattr(lead, "name", ""), "url": handle})
        elif not socials:
            needs_search.append({"name": getattr(lead, "name", ""),
                                 "company": getattr(lead, "company", ""),
                                 "city": getattr(lead, "city", "")})

    def read_one(lead):
        read = read_site(lead.site_url, max_pages=max_pages,
                         session=_thread_session())
        read.owner_match = check_owner(read, getattr(lead, "name", ""))
        return _read_key(lead), lead, read

    # The ledger is written from this loop rather than from `read_site`, for
    # two reasons: only here is the lead known (`read_site` takes a URL), and
    # only here is the code single-threaded again, so the appends are ordered
    # without contending for the lock on every page of every site.
    from outbound import ledger

    workers = max(1, min(workers, len(targets) or 1))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for key, lead, read in pool.map(read_one, targets):
            reads[key] = read
            for page in read.pages:
                ledger.record(lead_key=key, stage="fetch", platform="site",
                              url=page.url, retrieved_by="tier0", cost_usd=0.0,
                              secs=page.secs, outcome=page.outcome,
                              purpose="observe")
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
    elapsed = time.monotonic() - started
    unowned = [{"name": getattr(l, "name", ""), "url": l.site_url}
               for l in targets
               if reads.get(_read_key(l)) and reads[_read_key(l)].owner_match == "absent"]
    return {
        "reads": reads,
        "ok": sum(1 for r in reads.values() if r.ok),
        "attempted": attempted,
        "tier0_rate": round(sum(1 for r in reads.values() if r.ok) / attempted, 3)
        if attempted else 0.0,
        "elapsed_secs": round(elapsed, 1),
        "workers": workers,
        "escalate_plans": plans,
        "needs_search": needs_search,
        "ig_only": ig_only,
        "unowned": unowned,
        "report": (
            f"TIER 0: {sum(1 for r in reads.values() if r.ok)}/{attempted} sites "
            f"read free in {elapsed:.0f}s on {workers} worker(s). "
            f"{len(dead)} unreachable, {len(thin)} thin. "
            f"{len(plans)} batched Apify run(s) needed. "
            f"{len(needs_search)} lead(s) need a web search, "
            f"{len(ig_only)} reachable only on Instagram.\n"
            f"OWNER-CHECK: {len(unowned)}/{attempted} site(s) never mention the "
            f"lead's name. Advisory, never a kill — resolve each with a source "
            f"before spending on it."
        ),
    }
