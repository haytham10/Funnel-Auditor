"""
Platform/link-in-bio footprint classification — fetch-agnostic.

A hosted-platform footprint hides under two non-overlapping search shapes
(see PLATFORM_FOOTPRINTS below): the shared platform subdomain, and the
"Powered by X" footer signature every hosted funnel carries. This module
owns ONLY the merge/dedupe/noise-filter/tagging logic over hits already
fetched for both shapes — it never calls a search API itself, so either
fetch layer can feed it: Apify's google-search-scraper (`apify.footprint_search`,
the original path) or Firecrawl's `firecrawl_search` (already connected and
paid for in this environment, and the preferred path — it costs nothing
beyond what's already running, where every Apify call draws on the small
monthly cap shared with LinkedIn/Instagram, the one thing with no
substitute). `main.py classify-footprint` is the Firecrawl-fed CLI entry
point; a hit only needs a "url" key (title/description ride along if
present).

Moved out of audit/apify.py 2026-07-17 so the merge logic isn't duplicated
across fetch layers — `apify.py` re-exports PLATFORM_FOOTPRINTS, _host_of,
and _is_footprint_noise for backward compatibility (existing tests import
them off `apify`).
"""

from __future__ import annotations

from typing import Any


class FootprintError(RuntimeError):
    """Bad platform name or malformed hit input — never a fetch failure,
    since this module never fetches anything itself."""


# Each platform hides under two different, non-overlapping search shapes:
#   - `domain`: the shared platform subdomain. `site:mykajabi.com coach
#     Dubai` catches coaches still on the FREE default subdomain — usually
#     the less-established end.
#   - `marker`: the "Powered by X" footer signature every hosted funnel
#     carries. `"powered by kajabi" coach Dubai` (NO site restriction)
#     catches coaches on a CUSTOM domain still running the platform — the
#     more-invested, often better end, which the subdomain query is 100%
#     blind to (confirmed 2026-07-16: the subdomain and footer-signature
#     result sets barely overlapped, and achievher.com — a real Dubai
#     somatic coach on a custom domain — surfaced ONLY via the marker).
# Skool is community-first: its URLs are skool.com/<group> and it has no
# per-site funnel footer, so only the domain shape applies (marker None).
PLATFORM_FOOTPRINTS = {
    "kajabi":    {"domain": "mykajabi.com",  "marker": "powered by kajabi"},
    "teachable": {"domain": "teachable.com", "marker": "powered by teachable"},
    "thinkific": {"domain": "thinkific.com", "marker": "powered by thinkific"},
    "podia":     {"domain": "podia.com",     "marker": "powered by podia"},
    "systeme":   {"domain": "systeme.io",    "marker": "powered by systeme.io"},
    "kartra":    {"domain": "kartra.com",    "marker": "powered by kartra"},
    "skool":     {"domain": "skool.com",     "marker": None},
}

# Hosts the footer-signature net drags in that are never a coach's own
# funnel — their own platform marketing, and social/marketplace posts that
# merely mention the platform.
_FOOTPRINT_NOISE_HOSTS = (
    "kajabi.com", "teachable.com", "thinkific.com", "podia.com",
    "systeme.io", "kartra.com", "skool.com",
    "instagram.com", "facebook.com", "linkedin.com", "youtube.com",
    "twitter.com", "x.com", "tiktok.com", "pinterest.com", "reddit.com",
    "medium.com", "trustpilot.com", "g2.com", "capterra.com",
)


def _host_of(url: str) -> str:
    """Bare host (lowercased, no scheme/path/www) for per-site dedup."""
    u = url.split("://", 1)[-1]
    host = u.split("/", 1)[0].lower()
    return host[4:] if host.startswith("www.") else host


def _is_footprint_noise(url: str) -> bool:
    u = url.lower()
    # The platform's OWN root domain is noise; a coach's *.mykajabi.com
    # subdomain is not (that's a real free-tier funnel).
    for host in _FOOTPRINT_NOISE_HOSTS:
        if f"//{host}/" in u or f"//www.{host}/" in u or u.rstrip("/").endswith(f"//{host}"):
            return True
    return False


def queries_for(platform: str, geo: str = "Dubai", role: str = "coach") -> dict:
    """The two query strings a fetch layer should run for this platform, so
    Firecrawl (or anything else) knows exactly what to search without
    duplicating the shape logic. `marker_query` is None for skool."""
    key = platform.lower().strip()
    fp = PLATFORM_FOOTPRINTS.get(key)
    if not fp:
        raise FootprintError(
            f"unknown platform {key!r}; known: {', '.join(PLATFORM_FOOTPRINTS)}"
        )
    sub_q = f"{role} {geo}"
    marker_query = f'"{fp["marker"]}" {role} {geo}' if fp["marker"] else None
    return {
        "platform": key,
        "subdomain_query": f"site:{fp['domain']} {sub_q}",
        "marker_query": marker_query,
    }


def classify_footprint_hits(
    platform: str,
    subdomain_hits: list[dict] | None = None,
    marker_hits: list[dict] | None = None,
    *,
    geo: str = "Dubai",
    role: str = "coach",
) -> dict:
    """Merge + dedupe + tag pre-fetched hits from both query shapes.

    Dedupes by host, not full URL — one candidate per site. achievher.com/
    and achievher.com/login are the same coach; a coach's distinct
    *.mykajabi.com subdomain keeps its own host, so different free-tier
    coaches never collapse into each other. Drops the obvious non-funnel
    noise the wider footer-signature net drags in.

    Returns {"platform", "geo", "hits": [...], "subdomain_count",
    "footprint_count", "queries": [...]} — identical shape to
    `apify.footprint_search`, regardless of which layer did the fetching.
    """
    q = queries_for(platform, geo=geo, role=role)
    key = q["platform"]
    queries = [q["subdomain_query"]]
    if q["marker_query"]:
        queries.append(q["marker_query"])

    by_host: dict[str, dict] = {}
    sub_n = fp_n = 0

    for h in (subdomain_hits or []):
        if not isinstance(h, dict) or not h.get("url"):
            continue
        host = _host_of(h["url"])
        if host and host not in by_host:
            by_host[host] = {**h, "foundVia": "subdomain", "platform": key}
            sub_n += 1

    for h in (marker_hits or []):
        url = h.get("url", "") if isinstance(h, dict) else ""
        if not url or _is_footprint_noise(url):
            continue
        host = _host_of(url)
        if host and host not in by_host:
            by_host[host] = {**h, "foundVia": "footprint", "platform": key}
            fp_n += 1

    return {
        "platform": key,
        "geo": geo,
        "queries": queries,
        "subdomain_count": sub_n,
        "footprint_count": fp_n,
        "hits": list(by_host.values()),
    }
