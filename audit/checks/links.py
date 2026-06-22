"""Broken internal link detection via HEAD requests."""

import urllib.request
import urllib.error
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


_TIMEOUT = 10


def _same_host(url: str, base_url: str) -> bool:
    base_host = urlparse(base_url).netloc.lower()
    link_host = urlparse(url).netloc.lower()
    return base_host == link_host


def _head_status(url: str) -> int:
    try:
        req = urllib.request.Request(url, method="HEAD")
        req.add_header(
            "User-Agent",
            "Mozilla/5.0 (compatible; FunnelAuditor/1.0)",
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

        status = _head_status(absolute)
        if status == 0 or status >= 400:
            broken.append({"url": absolute, "status": status})

    return {
        "broken": broken,
        "total_checked": len(checked),
    }
