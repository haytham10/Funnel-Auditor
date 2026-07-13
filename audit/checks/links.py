"""Broken internal link detection via HEAD (with GET fallback) requests."""

import urllib.request
import urllib.error
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


_TIMEOUT = 10

# Only these read as genuinely dead. Bot walls (403/999), method rejections
# (405), and rate limits (429) are NOT evidence of a dead link.
_DEAD_STATUSES = {0, 404, 410}


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


def check_links(html: str, base_url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    broken: list[dict] = []
    unverifiable: list[dict] = []
    checked: set[str] = set()

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
        if absolute in checked:
            continue
        checked.add(absolute)

        status = _status(absolute, "HEAD")
        if status in (403, 404, 405, 429, 999):
            # Many hosts reject HEAD outright or gate bots on it — redirect/
            # proxy endpoints (e.g. Kajabi's resource_redirect/*) commonly
            # 404 a bare HEAD while resolving fine on GET. Retry once as GET
            # before trusting any of these statuses.
            status = _status(absolute, "GET")

        if status in _DEAD_STATUSES:
            broken.append({"url": absolute, "status": status})
        elif status in (403, 429, 999):
            unverifiable.append({"url": absolute, "status": status})

    return {
        "broken": broken,
        "unverifiable": unverifiable,
        "total_checked": len(checked),
    }
