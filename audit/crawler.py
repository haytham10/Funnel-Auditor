"""
Funnel crawler: walks a coach's bio link page, extracts funnel-relevant
destination URLs, fetches each with Playwright, and screenshots them at
desktop (1280px) and mobile (390px) widths.
"""

import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Page, Browser

from config import MAX_CRAWL_DEPTH, SCREENSHOT_DIR, FUNNEL_KEYWORDS, NOISE_DOMAINS, BIO_LINK_PLATFORMS


@dataclass
class CrawledPage:
    url: str
    title: str
    link_type: str          # "bio_page" | "sales" | "freebie" | "opt-in" | "course" | "direct"
    load_time_ms: float
    screenshot_desktop: str
    screenshot_mobile: str
    depth: int
    source_url: str = ""
    error: str = ""


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

    # Platform-specific anchor selectors
    selectors = {
        "linktree": "a[href]",
        "stan": "a[href]",
        "beacons": "a[href]",
        "direct": "a[href]",
    }
    selector = selectors.get(platform, "a[href]")

    for tag in soup.select(selector):
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

        # Skip self-links (same domain as bio page)
        bio_host = urlparse(base_url).netloc.lower()
        if parsed.netloc.lower() == bio_host:
            continue

        label = tag.get_text(separator=" ", strip=True) or tag.get("aria-label", "") or ""

        if _is_noise(absolute):
            noise_links.append({"url": absolute, "label": label, "category": "noise"})
            continue

        category = _funnel_category(absolute, label)
        if category:
            funnel_links.append({"url": absolute, "label": label, "category": category})
        else:
            # Unrecognised external link — include as "direct" for safety
            funnel_links.append({"url": absolute, "label": label, "category": "direct"})

    return funnel_links, noise_links


# ---------------------------------------------------------------------------
# Playwright helpers
# ---------------------------------------------------------------------------

def _safe_filename(url: str) -> str:
    """Turn a URL into a safe filename stem."""
    parsed = urlparse(url)
    stem = (parsed.netloc + parsed.path).strip("/").replace("/", "_")
    stem = re.sub(r"[^\w\-]", "_", stem)
    return stem[:80]


def _screenshot_path(url: str, suffix: str) -> str:
    Path(SCREENSHOT_DIR).mkdir(parents=True, exist_ok=True)
    filename = f"{_safe_filename(url)}_{suffix}.png"
    return str(Path(SCREENSHOT_DIR) / filename)


def _fetch_and_screenshot(
    page: Page,
    url: str,
    depth: int,
    link_type: str,
    source_url: str = "",
) -> CrawledPage:
    desktop_path = _screenshot_path(url, "desktop")
    mobile_path = _screenshot_path(url, "mobile")
    title = ""
    load_time_ms = 0.0
    error = ""

    try:
        # Desktop screenshot
        page.set_viewport_size({"width": 1280, "height": 800})
        t0 = time.perf_counter()
        page.goto(url, wait_until="networkidle", timeout=30_000)
        load_time_ms = (time.perf_counter() - t0) * 1000
        title = page.title()
        page.screenshot(path=desktop_path, full_page=True)

        # Mobile screenshot (same page, resize viewport)
        page.set_viewport_size({"width": 390, "height": 844})
        page.reload(wait_until="networkidle", timeout=30_000)
        page.screenshot(path=mobile_path, full_page=True)

    except Exception as exc:
        error = str(exc)
        # Create placeholder screenshot paths even on error
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
    )


# ---------------------------------------------------------------------------
# Main crawl entry point
# ---------------------------------------------------------------------------

def crawl(seed_url: str) -> CrawlResult:
    """
    Full crawl:
    1. Load the bio page, extract links.
    2. Screenshot the bio page.
    3. For each funnel-relevant link, fetch + screenshot (up to MAX_CRAWL_DEPTH).
    Returns a CrawlResult.
    """
    platform = detect_platform(seed_url)
    result = CrawlResult(seed_url=seed_url, platform=platform)

    with sync_playwright() as pw:
        browser: Browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()

        # --- Step 1: Crawl the bio page ---
        bio_page = _fetch_and_screenshot(
            page, seed_url, depth=0, link_type="bio_page"
        )
        result.pages.append(bio_page)

        # Get the rendered HTML for link extraction
        try:
            page.set_viewport_size({"width": 1280, "height": 800})
            page.goto(seed_url, wait_until="networkidle", timeout=30_000)
            html = page.content()
        except Exception as exc:
            bio_page.error = str(exc)
            browser.close()
            return result

        funnel_links, noise_links = extract_links(html, seed_url, platform)
        result.funnel_links = funnel_links
        result.noise_links = noise_links

        # --- Step 2: Crawl each funnel-relevant page ---
        depth = 1
        for link in funnel_links:
            if depth > MAX_CRAWL_DEPTH:
                break
            crawled = _fetch_and_screenshot(
                page,
                link["url"],
                depth=depth,
                link_type=link["category"],
                source_url=seed_url,
            )
            result.pages.append(crawled)
            depth += 1

        browser.close()

    return result
