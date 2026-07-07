"""
URL hygiene shared by the crawler, checks, and evidence layers.

Two jobs:
1. normalize() — one canonical form per page so `site.com`, `site.com/`,
   `site.com/#pricing`, and `site.com/?utm_source=ig` stop counting as four
   different pages and eating the crawl budget.
2. registrable_domain() / same_site() — "is this the lead's own site?"
   without an external tldextract dependency. Handles the two-level public
   suffixes these leads actually live on (co.uk, com.au, ie, ca, ...).
"""

import re
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

# Second-level labels that combine with a country code to form the public
# suffix (reflectiveparenting.co.uk → registrable domain reflectiveparenting.co.uk,
# not co.uk). Covers the markets this pipeline sources from.
_SECOND_LEVEL = {
    "co", "com", "org", "net", "ac", "gov", "edu", "or", "ne",
}

_TRACKING_PARAMS_RE = re.compile(
    r"^(utm_\w+|fbclid|gclid|mc_cid|mc_eid|ref|source)$", re.I
)


def normalize(url: str) -> str:
    """Canonical form: lowercase host, no fragment, no tracking params,
    no trailing slash (except root kept as bare host)."""
    parsed = urlparse(url.strip())
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    path = re.sub(r"/{2,}", "/", parsed.path).rstrip("/")
    query = urlencode(
        [(k, v) for k, v in parse_qsl(parsed.query)
         if not _TRACKING_PARAMS_RE.match(k)]
    )
    return urlunparse((parsed.scheme.lower() or "https", host, path, "", query, ""))


def registrable_domain(url_or_host: str) -> str:
    """example.co.uk for shop.example.co.uk; example.com for www.example.com."""
    host = url_or_host
    if "//" in host or "/" in host:
        host = urlparse(host if "//" in host else "//" + host).netloc or host.split("/")[0]
    host = host.lower().strip(".").lstrip("www.")
    labels = host.split(".")
    if len(labels) <= 2:
        return host
    # two-letter cc TLD with a known second-level label → keep three labels
    if len(labels[-1]) == 2 and labels[-2] in _SECOND_LEVEL:
        return ".".join(labels[-3:])
    return ".".join(labels[-2:])


def same_site(url_a: str, url_b: str) -> bool:
    """True when both URLs share a registrable domain — the lead's own site
    including subdomains (courses.her-site.com counts as hers)."""
    return registrable_domain(url_a) == registrable_domain(url_b)
