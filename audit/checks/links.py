"""Broken internal link detection via HEAD (with GET fallback) requests.

Checked concurrently (the requests are independent I/O waits) and cached
per process: a 16-page crawl of one site sees the same nav/footer links on
every page, and re-checking them serially with a 10s timeout each was the
single largest time cost in a walk. The cache is process-lifetime, which
equals crawl-lifetime for both fetch paths (`walk` and `ingest` are each
one process).
"""

import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


_TIMEOUT = 10
_MAX_WORKERS = 8
# New (uncached) links checked per page. Nav + footer + body CTAs fit well
# inside this; past it we're checking blog-roll pagination, not the funnel.
_MAX_NEW_LINKS_PER_PAGE = 25

# Only these read as genuinely dead. Bot walls (403/999), method rejections
# (405), and rate limits (429) are NOT evidence of a dead link.
_DEAD_STATUSES = {0, 404, 410}

# Statuses that warrant a GET retry after HEAD: hosts that reject HEAD
# outright or gate bots on it (Kajabi's resource_redirect/* 404s a bare
# HEAD while resolving fine on GET).
_RETRY_AS_GET = {403, 404, 405, 429, 999}

_status_cache: dict[str, int] = {}
_cache_lock = Lock()


def _same_host(url: str, base_url: str) -> bool:
    base_host = urlparse(base_url).netloc.lower()
    link_host = urlparse(url).netloc.lower()
    return base_host == link_host


def _status(url: str, method: str = "HEAD") -> int:
    try:
        req = urllib.request.Request(url, method=method)
        req.add_header(
            "User-Agent",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        )
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


def _resolve_status(url: str) -> int:
    status = _status(url, "HEAD")
    if status in _RETRY_AS_GET:
        status = _status(url, "GET")
    return status


def check_links(html: str, base_url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    broken: list[dict] = []
    unverifiable: list[dict] = []
    to_check: list[str] = []
    seen: set[str] = set()

    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        if not href or href.startswith("#") or href.startswith("javascript"):
            continue

        absolute = urljoin(base_url, href)
        parsed = urlparse(absolute)
        if parsed.scheme not in ("http", "https"):
            continue
        if not _same_host(absolute, base_url):
            continue
        if absolute in seen:
            continue
        seen.add(absolute)
        to_check.append(absolute)

    with _cache_lock:
        cached = {u: _status_cache[u] for u in to_check if u in _status_cache}
    fresh = [u for u in to_check if u not in cached][:_MAX_NEW_LINKS_PER_PAGE]

    results: dict[str, int] = dict(cached)
    if fresh:
        with ThreadPoolExecutor(max_workers=min(_MAX_WORKERS, len(fresh))) as pool:
            for url, status in zip(fresh, pool.map(_resolve_status, fresh)):
                results[url] = status
        with _cache_lock:
            _status_cache.update({u: results[u] for u in fresh})

    for url in to_check:
        status = results.get(url)
        if status is None:
            continue  # past the per-page cap this pass; caught on a later page or not at all
        if status in _DEAD_STATUSES:
            broken.append({"url": url, "status": status})
        elif status in (403, 429, 999):
            unverifiable.append({"url": url, "status": status})

    return {
        "broken": broken,
        "unverifiable": unverifiable,
        "total_checked": len(results),
    }
