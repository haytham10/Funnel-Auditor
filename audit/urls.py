"""
URL hygiene, shared by every stage that touches a link.

_Reworded 2026-07-31. It named "the crawler, checks, and evidence layers" as its
consumers; all three were deleted with the audit. The real callers now are
`normalize`, `dedupe`, `fetch`, `export`, `extract` and `email_enrich` — which
is more of the machine than before, not less._

Two jobs:
1. normalize() — one canonical form per page so `site.com`, `site.com/`,
   `site.com/#pricing`, and `site.com/?utm_source=ig` stop counting as four
   different pages, which is how a dedupe key stays stable and how a fetch
   plan stops paying twice for one page.
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


def strip_www(host: str) -> str:
    """Drop a leading 'www.' label — a real prefix strip, unlike
    lstrip('www.'), which is a character-set strip that also eats any leading
    run of w/. characters (wine.com -> ine.com, web.site.com -> eb.site.com).
    The one shared www-stripper: `registrable_domain`, `same_site` and the
    dedupe domain key all go through it, so they cannot disagree."""
    return host[4:] if host.startswith("www.") else host


def normalize(url: str) -> str:
    """Canonical form: https scheme, lowercase host, no fragment, no
    tracking params, no trailing slash (except root kept as bare host).

    Scheme is forced to https for dedupe purposes: a page's http:// and
    https:// variants are the same page (usually a stray un-upgraded
    template link), and treating them as distinct wasted crawl-budget
    slots re-fetching the same content twice."""
    parsed = urlparse(url.strip())
    host = strip_www(parsed.netloc.lower())
    path = re.sub(r"/{2,}", "/", parsed.path).rstrip("/")
    query = urlencode(
        [(k, v) for k, v in parse_qsl(parsed.query)
         if not _TRACKING_PARAMS_RE.match(k)]
    )
    return urlunparse(("https", host, path, "", query, ""))


def registrable_domain(url_or_host: str) -> str:
    """example.co.uk for shop.example.co.uk; example.com for www.example.com."""
    host = url_or_host
    if "//" in host or "/" in host:
        host = urlparse(host if "//" in host else "//" + host).netloc or host.split("/")[0]
    host = strip_www(host.lower().strip("."))
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


def slugify(value: str) -> str:
    """The one slug function, shared by the CLI (evidence folder name), the
    evidence packet builder, and the vision gate. Used to live duplicated in
    main.py and evidence.py — a real lead (Lynsey Ward, Jul 2026) got its IG
    screenshots and its site crawl written to two different evidence
    directories (evidence/momhoodmentor/ vs evidence/lynsey-ward/) because
    the two copies could independently drift, and a skill step guessed a
    slug by hand instead of calling either one. One function, always called
    the same way, is what keeps IG evidence and crawl evidence in the same
    folder so the vision gate can see both."""
    value = re.sub(r"^https?://(www\.)?", "", value.strip().lower())
    value = re.sub(r"[^\w]+", "-", value).strip("-")
    return value[:60] or "lead"
