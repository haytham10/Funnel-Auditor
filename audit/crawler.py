"""
Funnel crawler: walks a coach's bio link page, extracts funnel-relevant
destination URLs, fetches each with Playwright, screenshots them at
desktop (1280px) and mobile (390px) widths, and keeps the rendered HTML
for the checks/extraction layer.

Hop structure mirrors the 5-stop walk: bio page (Stop 1) → funnel pages
(Stops 2-3) → one more hop into checkout/buy links found on sales pages
(Stop 4).

Scope rules (hard-won from real walks):
- The lead's own site (same registrable domain, any subdomain) is always
  in scope — nav pages, pricing, courses, booking.
- External domains are in scope ONLY when they're funnel/booking platforms
  (Calendly, Kajabi, Stripe, ...). A radio station she was interviewed on,
  or the web designer credited in her footer, is NOT her funnel; those are
  recorded as external references and never crawled. One page max per
  external domain.
- Auth/login/account/search/legal pages never advance a walk; skipped.
- URLs are normalized (fragments, tracking params, trailing slashes)
  before dedupe, so #anchors don't triple-crawl the same page.
"""

import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

from config import (
    MAX_PAGES, MAX_CHECKOUT_HOPS, SCREENSHOT_DIR,
    NOISE_DOMAINS, BIO_LINK_PLATFORMS, CHECKOUT_LINK_KEYWORDS,
    EXTERNAL_FUNNEL_PLATFORMS, SKIP_PATH_RE, OFFER_PATH_HINTS,
    BOOKING_EMBED_HOSTS, JS_BUTTON_NOISE_RE, UNSAFE_CLICK_RE,
)
from audit.urls import normalize, same_site


@dataclass
class CrawledPage:
    url: str
    title: str
    link_type: str          # "bio_page" | "sales" | "freebie" | "opt-in" | "course" | "checkout" | "booking" | "direct"
    load_time_ms: float
    screenshot_desktop: str
    screenshot_mobile: str
    depth: int
    source_url: str = ""
    error: str = ""
    http_status: int = 0    # plain-request probe when the browser nav failed
    external: bool = False  # not on the lead's own site
    html: str = field(default="", repr=False)
    cta_clicks: list = field(default_factory=list)  # JS-only button click-discovery results


@dataclass
class CrawlResult:
    seed_url: str
    platform: str
    pages: list[CrawledPage] = field(default_factory=list)
    funnel_links: list[dict] = field(default_factory=list)   # {url, label, category}
    noise_links: list[dict] = field(default_factory=list)
    external_refs: list[dict] = field(default_factory=list)  # linked but out-of-scope, never crawled


# ---------------------------------------------------------------------------
# Platform detection
# ---------------------------------------------------------------------------

def detect_platform(url: str) -> str:
    """Return the bio-link platform name or 'direct'."""
    hostname = urlparse(url).netloc.lower().lstrip("www.")
    for platform, domains in BIO_LINK_PLATFORMS.items():
        for domain in domains:
            if hostname == domain or hostname.endswith("." + domain):
                return platform
    return "direct"


# ---------------------------------------------------------------------------
# Link extraction & classification
# ---------------------------------------------------------------------------

def _host_matches(url: str, domains: list[str] | tuple[str, ...]) -> bool:
    hostname = urlparse(url).netloc.lower().lstrip("www.")
    full = hostname + urlparse(url).path.lower()
    for d in domains:
        if "/" in d:
            if full.startswith(d) or full.startswith("www." + d):
                return True
        elif hostname == d or hostname.endswith("." + d):
            return True
    return False


def _is_noise(url: str) -> bool:
    return _host_matches(url, NOISE_DOMAINS)


def _is_external_platform(url: str) -> bool:
    return _host_matches(url, EXTERNAL_FUNNEL_PLATFORMS)


_LEGAL_RE = re.compile(r"/legal/|terms-of-service|terms-and-conditions|privacy-policy|/terms/?$|/privacy/?$", re.I)
_SKIP_PATH = re.compile(SKIP_PATH_RE, re.I)
_SKIP_LABELS = {
    "log in", "login", "sign in", "signin", "my account", "account",
    "search", "cookie policy", "cart",
}


def _is_legal(url: str, label: str) -> bool:
    return bool(_LEGAL_RE.search(url)) or label.strip().lower() in (
        "terms", "privacy", "privacy policy", "terms of service", "cookie policy", "imprint",
    )


def _is_skippable(url: str, label: str) -> bool:
    """Auth, account, search — pages that never advance a funnel walk."""
    if _SKIP_PATH.search(urlparse(url).path + "/"):
        return True
    return label.strip().lower() in _SKIP_LABELS


# Word-boundary keyword matching. The old substring version classified
# "judgement-free" as a freebie and "signature" as a signup. Hyphens count
# as word characters here ("judgement-free" must NOT match "free"; a URL
# slug like /free-guide still matches because "/" is a real boundary).
def _kw(*words: str) -> re.Pattern:
    return re.compile(
        r"(?<![\w-])(?:" + "|".join(words) + r")(?![\w-])", re.I
    )


_FREEBIE_KW = _kw("free", "freebie", "download", "checklist", "guide", "template", "gift")
_OPTIN_KW = _kw("opt-?in", "subscribe", "sign\\s?up", "newsletter", "waitlist", "wait\\s?list")
_COURSE_KW = _kw("courses?", "programs?", "masterclass", "bootcamp", "workshops?",
                 "trainings?", "membership", "classes", "intensive")
_SALES_KW = _kw("buy", "enroll", "join", "offers?", "sales?", "pricing", "prices",
                "invest(?:ment)?", "shop", "store", "services?", "packages?",
                "work with", "coaching")
_BOOKING_KW = _kw("book", "booking", "schedule", "calls?", "consult(?:ation)?s?",
                  "discovery", "appointment")
_OFFER_HINT_RE = re.compile("|".join(re.escape(h) for h in OFFER_PATH_HINTS), re.I)


def _funnel_category(url: str, label: str) -> str:
    """Best-guess category for a link that's already been scoped in.

    URL path hyphens are separators (/free-guide → "free guide"), label
    hyphens are compounds ("judgement-free" stays intact and must NOT
    match "free")."""
    path = urlparse(url).path.lower().replace("-", " ").replace("_", " ")
    text = f"{path} {label}".strip()

    if _is_external_platform(url):
        if _BOOKING_KW.search(text) or _host_matches(
            url, ["calendly.com", "acuityscheduling.com", "youcanbook.me",
                  "tidycal.com", "savvycal.com", "cal.com"]
        ):
            return "booking"
        if _FREEBIE_KW.search(text):
            return "freebie"
        return "sales"

    if _FREEBIE_KW.search(text):
        return "freebie"
    if _OPTIN_KW.search(text):
        return "opt-in"
    if _COURSE_KW.search(text):
        return "course"
    if _BOOKING_KW.search(text):
        return "booking"
    if _SALES_KW.search(text):
        return "sales"
    return "direct"


def extract_links(html: str, base_url: str, platform: str) -> tuple[list[dict], list[dict], list[dict]]:
    """
    Parse a page's links into (funnel_links, noise_links, external_refs).

    funnel_links   — crawlable: the lead's own pages + external funnel platforms,
                     sorted so offer-bearing pages get the budget first.
    noise_links    — socials/marketplaces, recorded not crawled.
    external_refs  — other external domains (press, designers, directories):
                     recorded for the judgment layer, never crawled.
    """
    soup = BeautifulSoup(html, "html.parser")
    funnel_links: list[dict] = []
    noise_links: list[dict] = []
    external_refs: list[dict] = []
    seen: set[str] = set()

    bio_parsed = urlparse(base_url)
    on_bio_platform = platform != "direct"
    profile_prefix = bio_parsed.path.rstrip("/")

    for tag in soup.select("a[href]"):
        href = tag.get("href", "").strip()
        if not href or href.startswith("#") or href.startswith("javascript"):
            continue

        absolute = urljoin(base_url, href)
        parsed = urlparse(absolute)
        if parsed.scheme not in ("http", "https"):
            continue

        canon = normalize(absolute)
        if canon in seen or canon == normalize(base_url):
            continue
        seen.add(canon)

        label = tag.get_text(separator=" ", strip=True) or tag.get("aria-label", "") or ""

        if _is_noise(absolute):
            noise_links.append({"url": absolute, "label": label, "category": "noise"})
            continue
        if _is_legal(absolute, label) or _is_skippable(absolute, label):
            continue

        if same_site(absolute, base_url):
            # On bio-link aggregators (Stan, Linktree, Beacons), same-host
            # links outside her profile path are other creators' profiles.
            # On her own self-hosted site, every internal page is hers.
            if on_bio_platform:
                own_subpage = (
                    profile_prefix
                    and parsed.path.startswith(profile_prefix + "/")
                    and parsed.path.rstrip("/") != profile_prefix
                )
                if not own_subpage:
                    continue
            funnel_links.append({
                "url": absolute, "label": label,
                "category": _funnel_category(absolute, label),
                "scope": "internal",
            })
        elif _is_external_platform(absolute):
            funnel_links.append({
                "url": absolute, "label": label,
                "category": _funnel_category(absolute, label),
                "scope": "external_platform",
            })
        else:
            # Press mentions, web-designer credits, podcast hosts, ...
            # Not her funnel. Never crawled, but kept visible.
            external_refs.append({"url": absolute, "label": label, "category": "external"})

    funnel_links.sort(key=_link_priority)
    return funnel_links, noise_links, external_refs


def _link_priority(link: dict) -> tuple:
    """Spend the page budget on offers first. Internal offer-path pages,
    then internal typed pages, then internal misc, then external platforms."""
    internal = link.get("scope") == "internal"
    path = urlparse(link["url"]).path
    offer_path = bool(_OFFER_HINT_RE.search(path))
    typed = link["category"] in ("sales", "course", "freebie", "opt-in", "booking")
    if internal and offer_path:
        rank = 0
    elif internal and typed:
        rank = 1
    elif internal:
        rank = 2
    else:
        rank = 3
    return (rank,)


def _discover_clickable_products(page: Page, seed_url: str, max_products: int = 6) -> list[dict]:
    """
    Bio platforms like Stan render product cards as JS buttons with no href —
    clicking is the only way to discover the product URLs. Click each distinct
    button, record where it routes, reset, repeat.
    """
    found: list[dict] = []
    seen_urls: set[str] = {normalize(seed_url)}
    seen_labels: set[str] = set()

    try:
        page.goto(seed_url, wait_until="networkidle", timeout=30_000)
    except Exception:
        return found

    buttons = page.locator("button")
    try:
        count = min(buttons.count(), 30)
    except Exception:
        return found

    for i in range(count):
        if len(found) >= max_products:
            break
        try:
            label = buttons.nth(i).inner_text(timeout=2_000).strip().replace("\n", " ")
        except Exception:
            continue
        if not label or len(label) > 60 or label in seen_labels:
            continue
        seen_labels.add(label)
        try:
            buttons.nth(i).click(timeout=3_000)
            page.wait_for_timeout(2_500)
            dest = normalize(page.url)
            if dest not in seen_urls:
                seen_urls.add(dest)
                category = _funnel_category(page.url, label)
                found.append({"url": page.url, "label": label,
                              "category": category if category != "direct" else "product",
                              "scope": "internal"})
            # Reset for the next click (goto is more reliable than go_back here)
            page.goto(seed_url, wait_until="networkidle", timeout=30_000)
        except Exception:
            try:
                page.goto(seed_url, wait_until="networkidle", timeout=30_000)
            except Exception:
                return found

    return found


_JS_BUTTON_NOISE_RE = re.compile(JS_BUTTON_NOISE_RE, re.I)
_UNSAFE_CLICK_RE = re.compile(UNSAFE_CLICK_RE, re.I)
_CTA_DISCOVERY_PAGE_TYPES = ("sales", "course", "booking")


def _discover_cta_destinations(page: Page, url: str, link_type: str, max_clicks: int = 6) -> list[dict]:
    """On a sales/course/booking page, a JS-only button (no href) is often
    the real path into a booking widget, an application form, or checkout —
    link extraction can't see it since there's no anchor to follow. Click
    each distinct one, record what happened (navigated to a new URL, an
    iframe/widget appeared in place, or nothing visible changed), then
    reset to the original page before trying the next.

    Scoped deliberately, not a general "click everything" crawler:
    - Only runs on sales/course/booking page types — never on a "checkout"
      page, where a real payment form could live.
    - Skips any button whose text reads as completing a payment or order
      (UNSAFE_CLICK_RE), even though that page type shouldn't have one —
      defense in depth on a live client's real site.
    - Skips nav/FAQ chrome (JS_BUTTON_NOISE_RE) so the click budget is
      spent on actual candidate CTAs.
    - Hard-capped click count, always resets via goto (not go_back) so a
      failed click can't leave the page in a broken state for whatever
      runs next.
    """
    found: list[dict] = []
    if link_type not in _CTA_DISCOVERY_PAGE_TYPES:
        return found

    try:
        buttons = page.locator("button")
        count = min(buttons.count(), 25)
    except Exception:
        return found

    clicks = 0
    seen_labels: set[str] = set()
    for i in range(count):
        if clicks >= max_clicks:
            break
        try:
            text = buttons.nth(i).inner_text(timeout=1_500).strip().replace("\n", " ")
        except Exception:
            continue
        if not text or len(text) > 80 or text in seen_labels:
            continue
        if _JS_BUTTON_NOISE_RE.search(text) or text.rstrip().endswith("?"):
            continue
        if _UNSAFE_CLICK_RE.search(text):
            found.append({"button_text": text, "destination": "skipped_unsafe"})
            continue
        seen_labels.add(text)

        try:
            before_url = normalize(page.url)
            before_iframes = page.locator("iframe").count()
            buttons.nth(i).click(timeout=3_000)
            page.wait_for_timeout(2_000)
            after_url = normalize(page.url)
            after_iframes = page.locator("iframe").count()

            if after_url != before_url:
                found.append({"button_text": text, "destination": "navigation", "url": page.url})
            elif after_iframes > before_iframes:
                new_srcs = []
                for j in range(before_iframes, after_iframes):
                    try:
                        src = page.locator("iframe").nth(j).get_attribute("src")
                    except Exception:
                        src = None
                    if src:
                        new_srcs.append(src)
                found.append({"button_text": text, "destination": "embedded_widget", "iframe_src": new_srcs})
            else:
                found.append({"button_text": text, "destination": "no_visible_change"})
            clicks += 1
            page.goto(url, wait_until="domcontentloaded", timeout=20_000)
            page.wait_for_timeout(500)
        except Exception:
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=20_000)
            except Exception:
                break

    return found


_CHECKOUT_KW = _kw("checkout", "buy", "enroll", "cart", "order", "register",
                   "purchase", "pay", "get access", "reserve", "reserve my (?:seat|spot)",
                   "save my (?:seat|spot)", "join now", "start now", "get started",
                   "sign up now", "claim my spot", "grab your spot", "book (?:your|my) (?:seat|spot)",
                   "add to cart", "get instant access")


def extract_checkout_links(html: str, base_url: str) -> list[dict]:
    """Find buy/enroll/checkout links on a sales or course page (Stop 4 hop).
    Same scope rules: her site or a payment/funnel platform, nothing else."""
    soup = BeautifulSoup(html, "html.parser")
    found: list[dict] = []
    seen: set[str] = set()

    for tag in soup.select("a[href]"):
        href = tag.get("href", "").strip()
        if not href or href.startswith("#") or href.startswith("javascript"):
            continue
        absolute = urljoin(base_url, href)
        if urlparse(absolute).scheme not in ("http", "https"):
            continue
        canon = normalize(absolute)
        if canon in seen or _is_noise(absolute):
            continue
        if not (same_site(absolute, base_url) or _is_external_platform(absolute)):
            continue
        label = tag.get_text(separator=" ", strip=True) or ""
        text = urlparse(absolute).path.lower() + " " + label
        if _CHECKOUT_KW.search(text):
            seen.add(canon)
            found.append({"url": absolute, "label": label, "category": "checkout"})
    return found


# ---------------------------------------------------------------------------
# Playwright helpers
# ---------------------------------------------------------------------------

def _safe_filename(url: str) -> str:
    """Turn a URL into a safe filename stem."""
    parsed = urlparse(url)
    stem = (parsed.netloc + parsed.path).strip("/").replace("/", "_")
    stem = re.sub(r"[^\w\-]", "_", stem)
    return stem[:80]


def _screenshot_path(url: str, suffix: str, screenshot_dir: str) -> str:
    Path(screenshot_dir).mkdir(parents=True, exist_ok=True)
    filename = f"{_safe_filename(url)}_{suffix}.png"
    return str(Path(screenshot_dir) / filename)


def _probe_status(context: BrowserContext, url: str) -> int:
    """Plain HTTP GET through the same proxy/context, no browser rendering.
    Distinguishes 'site is down' from 'site blocks headless browsers' —
    an HTTP 200 here with a failed nav means bot wall, not a dead link."""
    try:
        resp = context.request.get(url, timeout=15_000, max_redirects=5)
        return resp.status
    except Exception:
        return 0


def _goto_with_fallback(page: Page, url: str, timeout_ms: int = 30_000) -> None:
    """networkidle is the best signal but hangs on chatty pages (analytics
    long-polls, live chat). Fall back to domcontentloaded + settle."""
    try:
        page.goto(url, wait_until="networkidle", timeout=timeout_ms)
    except Exception:
        page.goto(url, wait_until="domcontentloaded", timeout=20_000)
        page.wait_for_timeout(4_000)


_BOOKING_EMBED_HOSTS = BOOKING_EMBED_HOSTS
# The iframe itself doesn't exist in the SSR'd HTML — an async widget script
# (e.g. assets.calendly.com/.../widget.js) injects it client-side, sometimes
# a beat after networkidle fires. Detect the container/script markers, which
# ARE present immediately, then wait for the iframe they produce.
_BOOKING_IFRAME_SELECTOR = ", ".join(f'iframe[src*="{h}"]' for h in _BOOKING_EMBED_HOSTS)
_BOOKING_MARKER_SELECTOR = ", ".join(
    f'[class*="{h.split(".")[0]}-inline-widget"], [data-url*="{h}"], script[src*="{h}"]'
    for h in _BOOKING_EMBED_HOSTS
) + ", " + _BOOKING_IFRAME_SELECTOR


def _wait_for_embeds(page: Page, timeout_ms: int = 8_000) -> None:
    """Inline booking widgets (Calendly and friends) render inside an iframe
    injected by an async script — the injection can land after networkidle,
    and the widget's own fetch for available slots happens inside that
    iframe, invisible to the parent page's network-idle signal. A screenshot
    taken right after goto/reload can catch the widget container present but
    still empty, producing a false 'no CTA here' read. Detect the container
    or script tag (present in the raw HTML immediately), then wait for the
    iframe it produces before any screenshot is taken."""
    try:
        if page.locator(_BOOKING_MARKER_SELECTOR).count() > 0:
            try:
                page.wait_for_selector(_BOOKING_IFRAME_SELECTOR, state="attached", timeout=timeout_ms)
            except Exception:
                pass
            page.wait_for_timeout(2_500)
    except Exception:
        pass


def _fetch_and_screenshot(
    page: Page,
    url: str,
    depth: int,
    link_type: str,
    screenshot_dir: str,
    source_url: str = "",
    external: bool = False,
) -> CrawledPage:
    desktop_path = _screenshot_path(url, "desktop", screenshot_dir)
    mobile_path = _screenshot_path(url, "mobile", screenshot_dir)
    title = ""
    load_time_ms = 0.0
    error = ""
    http_status = 0
    html = ""
    cta_clicks: list = []

    try:
        # Desktop screenshot + rendered HTML
        page.set_viewport_size({"width": 1280, "height": 800})
        t0 = time.perf_counter()
        _goto_with_fallback(page, url)
        load_time_ms = (time.perf_counter() - t0) * 1000
        title = page.title()
        _wait_for_embeds(page)
        html = page.content()
        page.screenshot(path=desktop_path, full_page=True)

        # Mobile screenshot (same page, resize viewport)
        page.set_viewport_size({"width": 390, "height": 844})
        try:
            page.reload(wait_until="networkidle", timeout=15_000)
        except Exception:
            page.wait_for_timeout(2_000)
        _wait_for_embeds(page)
        page.screenshot(path=mobile_path, full_page=True)

        # CTA click-discovery — after both screenshots, so clicking around
        # never disturbs the evidence captures. Scoped to sales/course/
        # booking pages only (see _discover_cta_destinations docstring).
        page.set_viewport_size({"width": 1280, "height": 800})
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=20_000)
            _wait_for_embeds(page)
            cta_clicks = _discover_cta_destinations(page, url, link_type)
        except Exception:
            cta_clicks = []

    except Exception as exc:
        error = str(exc)
        http_status = _probe_status(page.context, url)
        if http_status == 200:
            error += (
                " [HTTP probe: 200 — the site answers plain requests; this is "
                "a bot wall / heavy-JS render issue, NOT a dead link. Do not "
                "open on it as broken.]"
            )
        elif http_status:
            error += f" [HTTP probe: {http_status}]"
        else:
            error += " [HTTP probe also failed — site may genuinely be unreachable.]"
        desktop_path = desktop_path if Path(desktop_path).exists() else ""
        mobile_path = mobile_path if Path(mobile_path).exists() else ""

    return CrawledPage(
        url=url,
        title=title,
        link_type=link_type,
        load_time_ms=round(load_time_ms, 1),
        screenshot_desktop=desktop_path,
        screenshot_mobile=mobile_path,
        depth=depth,
        source_url=source_url,
        error=error,
        http_status=http_status,
        external=external,
        html=html,
        cta_clicks=cta_clicks,
    )


def _ensure_mitm_friendly_tls() -> None:
    """
    TLS-intercepting proxies (managed cloud sessions) can reset Chromium's
    post-quantum ClientHello. --disable-features doesn't reach this code path
    in current Chromium, but the enterprise policy does. Best-effort: skip
    silently anywhere we can't write /etc.
    """
    policy = '{"PostQuantumKeyAgreementEnabled": false, "EncryptedClientHelloEnabled": false}'
    for d in ("/etc/chromium/policies/managed", "/etc/opt/chrome/policies/managed"):
        try:
            Path(d).mkdir(parents=True, exist_ok=True)
            target = Path(d) / "funnel-auditor-tls.json"
            if not target.exists():
                target.write_text(policy)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Main crawl entry point
# ---------------------------------------------------------------------------

def crawl(seed_url: str, screenshot_dir: str | None = None) -> CrawlResult:
    """
    Full crawl:
    1. Load the bio page, extract + scope + prioritize links.
    2. Crawl the lead's own funnel pages (offer pages first), plus at most
       one page per external funnel platform.
    3. One more hop: checkout/buy links found on sales/course pages.
    Returns a CrawlResult with rendered HTML kept on every page.
    """
    screenshot_dir = screenshot_dir or SCREENSHOT_DIR
    platform = detect_platform(seed_url)
    result = CrawlResult(seed_url=seed_url, platform=platform)
    visited: set[str] = set()
    external_domains_crawled: set[str] = set()

    with sync_playwright() as pw:
        launch_kwargs: dict = {
            "headless": True,
            "args": ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
        }
        # Honor an explicitly provided Chromium (e.g. managed environments that
        # pre-install a browser instead of `playwright install`).
        exe = os.environ.get("FUNNEL_AUDITOR_CHROMIUM")
        if not exe:
            for candidate in ("/opt/pw-browsers/chromium",):
                if os.path.exists(candidate):
                    exe = candidate
                    break
        if exe:
            launch_kwargs["executable_path"] = exe
        # Managed environments route HTTPS through a local MITM proxy; Chromium
        # doesn't read proxy env vars on its own, so pass it through and accept
        # the proxy's certificate. On a normal machine neither branch fires.
        proxy_url = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
        proxied = bool(proxy_url and "127.0.0.1" in proxy_url)
        if proxied:
            launch_kwargs["proxy"] = {"server": proxy_url}
            _ensure_mitm_friendly_tls()
        browser: Browser = pw.chromium.launch(**launch_kwargs)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            ignore_https_errors=proxied,
        )
        page = context.new_page()

        # --- Step 1: Crawl the bio page ---
        bio_page = _fetch_and_screenshot(
            page, seed_url, depth=0, link_type="bio_page", screenshot_dir=screenshot_dir
        )
        result.pages.append(bio_page)
        visited.add(normalize(seed_url))

        if not bio_page.html:
            browser.close()
            return result

        funnel_links, noise_links, external_refs = extract_links(
            bio_page.html, seed_url, platform
        )

        # Bio platforms with JS product cards (Stan et al.) expose no hrefs —
        # discover products by clicking when anchor extraction found no own pages.
        if platform != "direct":
            has_own_pages = any(l.get("scope") == "internal" for l in funnel_links)
            if not has_own_pages:
                funnel_links.extend(_discover_clickable_products(page, seed_url))

        result.funnel_links = funnel_links
        result.noise_links = noise_links
        result.external_refs = external_refs

        # --- Step 2: Crawl each funnel-relevant page, offers first ---
        for link in funnel_links:
            if len(result.pages) >= MAX_PAGES:
                break
            canon = normalize(link["url"])
            if canon in visited:
                continue
            is_external = link.get("scope") == "external_platform"
            if is_external:
                from audit.urls import registrable_domain
                dom = registrable_domain(link["url"])
                if dom in external_domains_crawled:
                    continue
                external_domains_crawled.add(dom)
            visited.add(canon)
            crawled = _fetch_and_screenshot(
                page,
                link["url"],
                depth=1,
                link_type=link["category"],
                screenshot_dir=screenshot_dir,
                source_url=seed_url,
                external=is_external,
            )
            result.pages.append(crawled)

        # --- Step 3: follow the buy/enroll/reserve CTA all the way to the
        # real checkout — mandatory, not best-effort. A single hop from only
        # "sales/course/direct" pages missed real checkouts sitting behind
        # a freebie-then-upsell page, a booking page, or a second click
        # inside the checkout flow itself (reserve → payment). This now
        # runs multiple passes over EVERY page crawled so far (any type,
        # any depth, including pages discovered by an earlier pass), until
        # no new checkout links turn up or the hop budget is spent.
        checkout_hops = 0
        for _pass in range(4):
            if checkout_hops >= MAX_CHECKOUT_HOPS:
                break
            found_this_pass = False
            for crawled in list(result.pages):
                if checkout_hops >= MAX_CHECKOUT_HOPS or len(result.pages) >= MAX_PAGES + MAX_CHECKOUT_HOPS:
                    break
                if crawled.link_type == "checkout" or not crawled.html:
                    continue
                for co_link in extract_checkout_links(crawled.html, crawled.url):
                    if checkout_hops >= MAX_CHECKOUT_HOPS:
                        break
                    canon = normalize(co_link["url"])
                    if canon in visited:
                        continue
                    visited.add(canon)
                    result.pages.append(_fetch_and_screenshot(
                        page,
                        co_link["url"],
                        depth=crawled.depth + 1,
                        link_type="checkout",
                        screenshot_dir=screenshot_dir,
                        source_url=crawled.url,
                        external=not same_site(co_link["url"], seed_url),
                    ))
                    checkout_hops += 1
                    found_this_pass = True
            if not found_this_pass:
                break

        browser.close()

    return result
