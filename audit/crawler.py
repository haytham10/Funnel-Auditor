"""
Funnel crawler: walks a coach's bio link page, extracts funnel-relevant
destination URLs, fetches each with Playwright, screenshots them at
desktop (1280px) and mobile (390px) widths, and keeps the rendered HTML
for the checks/extraction layer.

Hop structure mirrors the 5-stop walk: bio page (Stop 1) → funnel pages
(Stops 2-3) → one more hop into checkout/buy links found on sales pages
(Stop 4).
"""

import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Page, Browser

from config import (
    MAX_PAGES, MAX_CHECKOUT_HOPS, SCREENSHOT_DIR,
    NOISE_DOMAINS, BIO_LINK_PLATFORMS, CHECKOUT_LINK_KEYWORDS,
)


@dataclass
class CrawledPage:
    url: str
    title: str
    link_type: str          # "bio_page" | "sales" | "freebie" | "opt-in" | "course" | "checkout" | "direct"
    load_time_ms: float
    screenshot_desktop: str
    screenshot_mobile: str
    depth: int
    source_url: str = ""
    error: str = ""
    html: str = field(default="", repr=False)


@dataclass
class CrawlResult:
    seed_url: str
    platform: str
    pages: list[CrawledPage] = field(default_factory=list)
    funnel_links: list[dict] = field(default_factory=list)   # {url, label, category}
    noise_links: list[dict] = field(default_factory=list)


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

def _is_noise(url: str) -> bool:
    hostname = urlparse(url).netloc.lower().lstrip("www.")
    return any(hostname == nd or hostname.endswith("." + nd) for nd in NOISE_DOMAINS)


_LEGAL_RE = re.compile(r"/legal/|terms-of-service|terms-and-conditions|privacy-policy|/terms/?$|/privacy/?$", re.I)


def _is_legal(url: str, label: str) -> bool:
    return bool(_LEGAL_RE.search(url)) or label.strip().lower() in (
        "terms", "privacy", "privacy policy", "terms of service", "cookie policy", "imprint",
    )


def _funnel_category(url: str, label: str) -> str | None:
    """
    Return a funnel category string if the link looks funnel-relevant,
    else None.
    """
    text = (url + " " + label).lower()

    # Platform-hosted stores are always funnel-relevant
    funnel_platforms = [
        "kajabi.com", "teachable.com", "thinkific.com", "podia.com",
        "samcart.com", "clickfunnels.com", "kartra.com", "systeme.io",
        "gumroad.com", "payhip.com", "lemonsqueezy.com", "stan.store",
        "whop.com",
    ]
    hostname = urlparse(url).netloc.lower().lstrip("www.")
    for fp in funnel_platforms:
        if hostname == fp or hostname.endswith("." + fp):
            if any(k in text for k in ("free", "freebie", "download", "checklist", "guide", "template")):
                return "freebie"
            if any(k in text for k in ("opt", "subscribe", "signup", "sign up", "join")):
                return "opt-in"
            return "sales"

    # Keyword-based classification
    if any(k in text for k in ("free", "freebie", "download", "checklist", "guide", "template", "gift")):
        return "freebie"
    if any(k in text for k in ("opt-in", "optin", "subscribe", "signup", "sign up", "newsletter")):
        return "opt-in"
    if any(k in text for k in ("course", "program", "masterclass", "bootcamp", "workshop", "training", "membership")):
        return "course"
    if any(k in text for k in ("buy", "enroll", "join", "offer", "sales", "book", "schedule", "call", "consult", "coaching")):
        return "sales"

    return None


def extract_links(html: str, base_url: str, platform: str) -> tuple[list[dict], list[dict]]:
    """
    Parse the bio page HTML and split links into funnel-relevant and noise.
    Returns (funnel_links, noise_links) where each item is {url, label, category}.
    """
    soup = BeautifulSoup(html, "html.parser")
    funnel_links: list[dict] = []
    noise_links: list[dict] = []
    seen: set[str] = set()

    bio_parsed = urlparse(base_url)
    bio_host = bio_parsed.netloc.lower()
    # On bio platforms (Stan, Linktree, Beacons) the lead's own product pages
    # live on the SAME host under her profile path (stan.store/<handle>/p/...).
    # Same-host links outside her profile path are other profiles / platform
    # pages and get skipped.
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

        # Deduplicate
        if absolute in seen:
            continue
        seen.add(absolute)

        # Same-host links: keep only the lead's own sub-pages on bio platforms
        if parsed.netloc.lower() == bio_host:
            own_subpage = (
                on_bio_platform
                and profile_prefix
                and parsed.path.startswith(profile_prefix + "/")
                and parsed.path.rstrip("/") != profile_prefix
            )
            if not own_subpage:
                continue

        label = tag.get_text(separator=" ", strip=True) or tag.get("aria-label", "") or ""

        if _is_noise(absolute):
            noise_links.append({"url": absolute, "label": label, "category": "noise"})
            continue
        if _is_legal(absolute, label):
            continue

        category = _funnel_category(absolute, label)
        if category:
            funnel_links.append({"url": absolute, "label": label, "category": category})
        else:
            # Unrecognised external link — include as "direct" for safety
            funnel_links.append({"url": absolute, "label": label, "category": "direct"})

    return funnel_links, noise_links


def _discover_clickable_products(page: Page, seed_url: str, max_products: int = 6) -> list[dict]:
    """
    Bio platforms like Stan render product cards as JS buttons with no href —
    clicking is the only way to discover the product URLs. Click each distinct
    button, record where it routes, reset, repeat.
    """
    found: list[dict] = []
    seen_urls: set[str] = {seed_url.rstrip("/")}
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
            dest = page.url.rstrip("/")
            if dest not in seen_urls:
                seen_urls.add(dest)
                category = _funnel_category(dest, label) or "product"
                found.append({"url": page.url, "label": label, "category": category})
            # Reset for the next click (goto is more reliable than go_back here)
            page.goto(seed_url, wait_until="networkidle", timeout=30_000)
        except Exception:
            try:
                page.goto(seed_url, wait_until="networkidle", timeout=30_000)
            except Exception:
                return found

    return found


def extract_checkout_links(html: str, base_url: str) -> list[dict]:
    """Find buy/enroll/checkout links on a sales or course page (Stop 4 hop)."""
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
        if absolute in seen or _is_noise(absolute):
            continue
        label = tag.get_text(separator=" ", strip=True) or ""
        text = (absolute + " " + label).lower()
        if any(k in text for k in CHECKOUT_LINK_KEYWORDS):
            seen.add(absolute)
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


def _fetch_and_screenshot(
    page: Page,
    url: str,
    depth: int,
    link_type: str,
    screenshot_dir: str,
    source_url: str = "",
) -> CrawledPage:
    desktop_path = _screenshot_path(url, "desktop", screenshot_dir)
    mobile_path = _screenshot_path(url, "mobile", screenshot_dir)
    title = ""
    load_time_ms = 0.0
    error = ""
    html = ""

    try:
        # Desktop screenshot + rendered HTML
        page.set_viewport_size({"width": 1280, "height": 800})
        t0 = time.perf_counter()
        page.goto(url, wait_until="networkidle", timeout=30_000)
        load_time_ms = (time.perf_counter() - t0) * 1000
        title = page.title()
        html = page.content()
        page.screenshot(path=desktop_path, full_page=True)

        # Mobile screenshot (same page, resize viewport)
        page.set_viewport_size({"width": 390, "height": 844})
        page.reload(wait_until="networkidle", timeout=30_000)
        page.screenshot(path=mobile_path, full_page=True)

    except Exception as exc:
        error = str(exc)
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
        html=html,
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
    1. Load the bio page, extract links.
    2. Screenshot the bio page.
    3. For each funnel-relevant link, fetch + screenshot.
    4. One more hop: checkout/buy links found on sales/course pages.
    Returns a CrawlResult with rendered HTML kept on every page.
    """
    screenshot_dir = screenshot_dir or SCREENSHOT_DIR
    platform = detect_platform(seed_url)
    result = CrawlResult(seed_url=seed_url, platform=platform)
    visited: set[str] = set()

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
        visited.add(seed_url)

        if not bio_page.html:
            browser.close()
            return result

        funnel_links, noise_links = extract_links(bio_page.html, seed_url, platform)

        # Bio platforms with JS product cards (Stan et al.) expose no hrefs —
        # discover products by clicking when anchor extraction found no own pages.
        if platform != "direct":
            seed_host = urlparse(seed_url).netloc.lower()
            has_own_pages = any(
                urlparse(l["url"]).netloc.lower() == seed_host for l in funnel_links
            )
            if not has_own_pages:
                funnel_links.extend(_discover_clickable_products(page, seed_url))

        result.funnel_links = funnel_links
        result.noise_links = noise_links

        # --- Step 2: Crawl each funnel-relevant page ---
        for link in funnel_links:
            if len(result.pages) >= MAX_PAGES:
                break
            if link["url"] in visited:
                continue
            visited.add(link["url"])
            crawled = _fetch_and_screenshot(
                page,
                link["url"],
                depth=1,
                link_type=link["category"],
                screenshot_dir=screenshot_dir,
                source_url=seed_url,
            )
            result.pages.append(crawled)

        # --- Step 3: One more hop into checkouts from sales/course pages ---
        checkout_hops = 0
        for crawled in list(result.pages):
            if checkout_hops >= MAX_CHECKOUT_HOPS or len(result.pages) >= MAX_PAGES + MAX_CHECKOUT_HOPS:
                break
            if crawled.depth != 1 or crawled.link_type not in ("sales", "course", "direct"):
                continue
            if not crawled.html:
                continue
            for co_link in extract_checkout_links(crawled.html, crawled.url):
                if checkout_hops >= MAX_CHECKOUT_HOPS:
                    break
                if co_link["url"] in visited:
                    continue
                visited.add(co_link["url"])
                result.pages.append(_fetch_and_screenshot(
                    page,
                    co_link["url"],
                    depth=2,
                    link_type="checkout",
                    screenshot_dir=screenshot_dir,
                    source_url=crawled.url,
                ))
                checkout_hops += 1

        browser.close()

    return result
