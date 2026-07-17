"""
Apify actor integration — the no-login third-party fetch layer.

Firecrawl (the primary fetcher) hard-refuses LinkedIn and does not do
authenticated Instagram, so the two login-walled platforms that carry the
best SMYKM hook evidence have no fetch path on their own. This module is
that path: read-only public data pulled through vetted Apify actors that
take a username or URL and need no account — exactly what the hard rules
allow (`enrichment and SMYKM hook-finding ... Instagram the same as
LinkedIn`, never logging in or acting as Haytham anywhere).

It also wraps email verification (the `email-check` WARN → verify fallback,
and the confirm-before-CRM step for a found address) and a Google SERP
scraper (sourcing + finding episode / About / profile pages).

Everything web-fetchable (podcasts, YouTube, About pages, funnel walks,
checkout probes) stays on Firecrawl, which is cheaper and already
connected. This layer is deliberately small: the five Haytham-vetted
actors below and nothing else. Adding actors is surface area and cost, not
capability.

Email verification and Google-footprint sourcing no longer default to this
layer (2026-07-17, after the free plan's small monthly USD cap kept getting
hit). `verify_emails`/`google_search`/`footprint_search` below still work
and stay as a manual fallback, but the default paths are now
`audit/email_verifier.py` (ZeroBounce, its own free tier, no Apify billing)
and `audit/footprint.py` fed by Firecrawl search (`main.py
classify-footprint`) — both keep the monthly cap free for LinkedIn/
Instagram, the one thing Firecrawl genuinely can't reach.

## The actor set (vetted; do not expand casually)

    ig          apify/instagram-scraper                 profile details + recent posts w/ captions (date-filterable); post detail
    li_posts    harvestapi/linkedin-profile-posts       recent posts w/ text + date (no cookies) — where LinkedIn hooks live
    li_profile  apimaestro/linkedin-profile-detail      headline/about/experience; optional email-search mode (finds an address)
    email       account56/email-verifier                MillionVerifier-backed address verification
    search      apify/google-search-scraper             Google SERP (site:, country, date filters)

    (li_profile switched from harvestapi/linkedin-profile-scraper to
    apimaestro/linkedin-profile-detail 2026-07-16 — the harvestapi PROFILE
    actor specifically enforces its own ~20-runs/month quota independent of
    Apify billing, and a batch hit it mid-run. li_posts stays on harvestapi:
    that actor isn't capped and is roughly 2.5x cheaper per post than
    apimaestro's equivalent — confirmed by comparing run costs in the Apify
    console after a brief mis-swap of both actors together. Don't swap
    li_posts again without re-confirming the cap actually applies to it.)

## Cost discipline (Instagram and the email-search mode are the pricey ones)

- LinkedIn: posts-first. `linkedin_posts` is where a recent-post hook comes
  from; only reach for `linkedin_profile` when you actually need the
  About/career story and the site didn't already give it. Never both by
  default.
- Instagram: `instagram(..., mode="posts", newer_than=...)` with a small
  limit; only `instagram_post` on a specific post that looks like a hook
  and needs its full detail. Extract useful fields only (this module trims
  by default; `--raw` bypasses it for debugging).
- Email: the no-email profile mode is $4/1k, the email-search mode is
  $10/1k — only pass `with_email=True` when you're actually hunting an
  address. Never re-verify an address already MX-confirmed.
- Search: tight scoped queries, low page counts.

## The token

Reads `APIFY_TOKEN` (or `APIFY_API_TOKEN`) from the environment — it lives
as an env secret on the runner, never in code or the repo. Actor discovery
(`discover_actors`) hits the public Store and needs no token; every run
does. A missing token fails closed with a clear message, never a guess.
"""

from __future__ import annotations

import os
from typing import Any

import requests

from audit.footprint import (  # re-exported for backward compat (tests import these off `apify`)
    PLATFORM_FOOTPRINTS,
    _host_of,
    _is_footprint_noise,
    classify_footprint_hits,
)

APIFY_BASE = "https://api.apify.com/v2"

# Haytham-vetted actors, addressed in the `username~actor-name` form the
# REST API uses. Keep this map tight.
ACTORS = {
    "ig": "apify~instagram-scraper",
    "li_posts": "harvestapi~linkedin-profile-posts",
    "li_profile": "apimaestro~linkedin-profile-detail",
    "email": "account56~email-verifier",
    "search": "apify~google-search-scraper",
}

# Default sync-run ceiling. run-sync-get-dataset-items holds the HTTP
# connection open until the run finishes or this elapses; a run that
# overruns returns 408 and should be re-issued async (run_actor_async).
_SYNC_TIMEOUT_SECS = 240

LI_POSTED_LIMITS = ("any", "1h", "24h", "week", "month", "3months", "6months", "year")
IG_RESULT_TYPES = ("posts", "details", "comments", "reels", "mentions", "stories")


class ApifyError(RuntimeError):
    """Any Apify-side failure: missing token, billing, timeout, bad input."""


def _token() -> str:
    tok = os.environ.get("APIFY_TOKEN") or os.environ.get("APIFY_API_TOKEN")
    if not tok:
        raise ApifyError(
            "APIFY_TOKEN is not set. This runner needs the token as an "
            "environment secret (APIFY_TOKEN). Discovery (apify actors <q>) "
            "works without it; every actor run needs it."
        )
    return tok


def _auth_headers() -> dict[str, str]:
    # Token in the Authorization header, never the URL/query — keeps it out
    # of logs and process listings.
    return {"Authorization": f"Bearer {_token()}"}


def run_actor(
    actor_id: str,
    run_input: dict[str, Any],
    *,
    timeout_secs: int = _SYNC_TIMEOUT_SECS,
    memory_mbytes: int | None = None,
) -> list[dict]:
    """Run an actor synchronously and return its dataset items.

    POSTs to run-sync-get-dataset-items, which blocks until the run ends and
    returns the dataset in one shot. Raises ApifyError with an actionable
    message on the failures worth distinguishing (bad token, no credits,
    sync timeout).
    """
    params: dict[str, Any] = {"timeout": timeout_secs}
    if memory_mbytes:
        params["memory"] = memory_mbytes
    try:
        resp = requests.post(
            f"{APIFY_BASE}/acts/{actor_id}/run-sync-get-dataset-items",
            params=params,
            json=run_input,
            headers=_auth_headers(),
            timeout=timeout_secs + 30,
        )
    except requests.RequestException as exc:
        raise ApifyError(f"network error reaching Apify: {exc}") from exc

    if resp.status_code == 401:
        raise ApifyError("401 Unauthorized — APIFY_TOKEN is missing or invalid.")
    if resp.status_code == 402:
        raise ApifyError("402 Payment Required — the Apify account is out of credits or billing is not set up.")
    if resp.status_code in (408, 504):
        raise ApifyError(
            f"{resp.status_code} — the run exceeded the {timeout_secs}s sync window. "
            "Re-issue with a longer --timeout, a smaller limit, or the async path."
        )
    if not resp.ok:
        raise ApifyError(f"{resp.status_code} from Apify: {resp.text[:400]}")
    try:
        data = resp.json()
    except ValueError as exc:
        raise ApifyError(f"non-JSON response from Apify: {resp.text[:200]}") from exc
    return data if isinstance(data, list) else [data]


def account_limits() -> dict:
    """Current monthly usage vs. plan limits (`GET /v2/users/me/limits`) —
    the same figures shown on the account's Limits page. Costs nothing to
    call and needs no actor run.

    Added after a batch-audit run (evening prep, Jul 15 2026) burned extra
    tool calls when several lead-processor agents each independently
    discovered a dead monthly quota by running actors into it one at a
    time. This lets an orchestrator check once, up front, and skip Apify
    entirely for the rest of a batch instead of every subagent re-learning
    the same fact the expensive way.

    Returns the raw `limits`/`current` blocks plus a computed
    `pct_of_usd_cap` and `near_cap` (>=90% of `maxMonthlyUsageUsd`) — the
    single plan-agnostic signal, since the USD budget is what actually caps
    a free/starter account regardless of which actor is being run.
    """
    try:
        resp = requests.get(
            f"{APIFY_BASE}/users/me/limits",
            headers=_auth_headers(),
            timeout=30,
        )
    except requests.RequestException as exc:
        raise ApifyError(f"network error reaching Apify: {exc}") from exc
    if resp.status_code == 401:
        raise ApifyError("401 Unauthorized — APIFY_TOKEN is missing or invalid.")
    if not resp.ok:
        raise ApifyError(f"{resp.status_code} from Apify: {resp.text[:400]}")
    try:
        data = resp.json().get("data", {})
    except ValueError as exc:
        raise ApifyError(f"non-JSON response from Apify: {resp.text[:200]}") from exc

    limits = data.get("limits", {}) or {}
    current = data.get("current", {}) or {}
    usd_cap = limits.get("maxMonthlyUsageUsd") or 0
    usd_used = current.get("monthlyUsageUsd") or 0
    pct = round(100 * usd_used / usd_cap, 1) if usd_cap else None
    return {
        "monthly_usage_cycle": data.get("monthlyUsageCycle", {}),
        "limits": limits,
        "current": current,
        "pct_of_usd_cap": pct,
        "near_cap": pct is not None and pct >= 90,
    }


def discover_actors(query: str, limit: int = 6) -> list[dict]:
    """Search the public Apify Store (no token needed). Returns a ranked,
    trimmed list — how the actor set was chosen in the first place."""
    try:
        resp = requests.get(
            f"{APIFY_BASE}/store",
            params={"search": query, "limit": limit},
            timeout=30,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise ApifyError(f"network error reaching Apify Store: {exc}") from exc
    items = resp.json().get("data", {}).get("items", [])
    out = []
    for a in items:
        stats = a.get("stats", {}) or {}
        out.append({
            "id": f"{a.get('username')}/{a.get('name')}",
            "title": a.get("title"),
            "totalRuns": stats.get("totalRuns"),
        })
    return out


# --------------------------------------------------------------------------
# Field trimming — keep the useful signal, drop the noise (base64 media,
# raw html, giant nested blobs) so a hook search doesn't drown in tokens or
# a dataset blow the context. `raw=True` on any wrapper bypasses this.
# --------------------------------------------------------------------------

_NOISE_KEYS = {
    "displayUrl", "images", "videoUrl", "html", "rawHtml", "base64",
    "profilePicUrl", "profilePicUrlHD", "childPosts", "musicInfo",
    "taggedUsers", "coauthorProducers", "sidecar",
}


def _lean(item: dict, keep: tuple[str, ...] | None = None) -> dict:
    if not isinstance(item, dict):
        return item
    if keep:
        return {k: item[k] for k in keep if k in item and item[k] not in (None, "", [])}
    return {k: v for k, v in item.items() if k not in _NOISE_KEYS}


def instagram(url: str, mode: str = "posts", newer_than: str | None = None,
              limit: int = 12, raw: bool = False) -> list[dict]:
    """Instagram profile enrichment. mode='details' → profile metadata
    (followers, bio, latest posts); mode='posts' → recent posts with
    captions, `newer_than` (e.g. '7 days', '2026-07-01') filtering recency."""
    if mode not in IG_RESULT_TYPES:
        raise ApifyError(f"instagram mode must be one of {IG_RESULT_TYPES}, got {mode!r}")
    run: dict[str, Any] = {
        "directUrls": [url],
        "resultsType": mode,
        "resultsLimit": limit,
        "addParentData": False,
    }
    if newer_than:
        run["onlyPostsNewerThan"] = newer_than
    items = run_actor(ACTORS["ig"], run, memory_mbytes=1024)
    if raw:
        return items
    keep = ("username", "fullName", "biography", "followersCount", "postsCount",
            "url", "latestPosts") if mode == "details" else \
           ("ownerUsername", "shortCode", "url", "timestamp", "caption",
            "likesCount", "commentsCount", "type", "hashtags")
    return [_lean(i, keep) for i in items]


def instagram_post(post_url: str, raw: bool = False) -> list[dict]:
    """Full detail on one IG post — the deeper dig once a post looks like a
    hook (caption in full plus top comments)."""
    items = run_actor(
        ACTORS["ig"],
        {"directUrls": [post_url], "resultsType": "posts", "resultsLimit": 1,
         "addParentData": False},
        memory_mbytes=1024,
    )
    if raw:
        return items
    return [_lean(i, ("ownerUsername", "shortCode", "url", "timestamp", "caption",
                      "likesCount", "commentsCount", "type", "latestComments"))
            for i in items]


def linkedin_posts(url: str, max_posts: int = 5, since: str | None = None,
                   raw: bool = False) -> list[dict]:
    """Recent LinkedIn posts (no cookies) — the primary hook source. `since`
    is one of LI_POSTED_LIMITS (e.g. 'week', 'month'). Reactions/comments
    stay off by default to keep the run cheap."""
    if since and since not in LI_POSTED_LIMITS:
        raise ApifyError(f"since must be one of {LI_POSTED_LIMITS}, got {since!r}")
    run: dict[str, Any] = {"targetUrls": [url], "maxPosts": max_posts}
    if since:
        run["postedLimit"] = since
    items = run_actor(ACTORS["li_posts"], run, memory_mbytes=256)
    if raw:
        return items
    return [_lean(i, ("linkedinUrl", "postedAt", "postedDate", "content",
                      "text", "type", "reactionsCount", "commentsCount",
                      "repostsCount", "author"))
            for i in items]


def linkedin_profile(url: str, with_email: bool = False, raw: bool = False) -> list[dict]:
    """LinkedIn profile enrichment (headline, about, experience). Pass
    with_email=True ONLY when hunting an address for a no-email lead. Takes
    a profile URL or bare username."""
    items = run_actor(ACTORS["li_profile"], {"username": url, "includeEmail": with_email},
                       memory_mbytes=256)
    if raw:
        return items
    out = []
    for i in items:
        info = i.get("basic_info") or {}
        location = info.get("location") or {}
        experience = [
            {k: e.get(k) for k in
             ("title", "company", "location", "duration", "description", "is_current")
             if e.get(k) not in (None, "", [])}
            for e in (i.get("experience") or [])
        ]
        rec = {
            "linkedinUrl": info.get("profile_url"),
            "publicIdentifier": info.get("public_identifier"),
            "fullName": info.get("fullname"),
            "headline": info.get("headline"),
            "about": info.get("about"),
            "location": location.get("full"),
            "currentCompany": info.get("current_company"),
            "followerCount": info.get("follower_count"),
            "website": info.get("creator_website"),
            "email": info.get("email"),
            "experience": experience,
        }
        out.append({k: v for k, v in rec.items() if v not in (None, "", [])})
    return out


def verify_emails(emails: list[str], raw: bool = False) -> list[dict]:
    """Verify one or more addresses (MillionVerifier-backed). The confirm
    step before a found/guessed address enters the CRM."""
    if not emails:
        raise ApifyError("verify_emails needs at least one address")
    items = run_actor(ACTORS["email"], {"emails": emails}, memory_mbytes=256)
    if raw:
        return items
    return [_lean(i, ("email", "status", "result", "resultCode", "subStatus",
                      "free", "role", "disposable"))
            for i in items]


def google_search(query: str, pages: int = 1, site: str | None = None,
                  country: str | None = "ae", raw: bool = False,
                  meta: bool = False) -> list[dict] | dict:
    """Google SERP for one query. `site` scopes to a domain (e.g.
    linkedin.com), `country` biases results (default UAE).

    The apify google-search-scraper returns far more per hit than a plain
    search snippet, and the extra fields earn their keep for sourcing:
    - `websiteTitle` — the site/platform label Google shows (e.g.
      "mykajabi.com"), a free platform tag before any scrape.
    - `emphasizedKeywords` — the exact query terms Google bolded in the
      snippet. On a footer-signature query ("powered by kajabi ..."), a
      hit whose emphasizedKeywords actually contains the marker is a real
      match, not a stray Google guess — this is the false-positive filter
      for the footprint channel.
    With `meta=True` the return is a dict that also carries the page-level
    `relatedQueries` and `peopleAlsoAsk` (query-expansion fuel for lateral
    discovery) plus `resultsTotal`; otherwise it's the flat hit list, as
    before (backward compatible)."""
    run: dict[str, Any] = {"queries": query, "maxPagesPerQuery": pages}
    if site:
        run["site"] = site
    if country:
        run["countryCode"] = country
    items = run_actor(ACTORS["search"], run, memory_mbytes=1024)
    if raw:
        return items
    # The SERP actor returns one item per results page; flatten organic hits.
    hits: list[dict] = []
    related: list = []
    also_ask: list = []
    for page in items:
        if not isinstance(page, dict):
            continue
        for r in page.get("organicResults", []):
            hits.append(_lean(r, ("title", "url", "displayedUrl", "websiteTitle",
                                  "description", "emphasizedKeywords")))
        related.extend(page.get("relatedQueries", []) or [])
        also_ask.extend(page.get("peopleAlsoAsk", []) or [])
    hits = hits or items
    if not meta:
        return hits
    return {
        "hits": hits,
        "relatedQueries": related,
        "peopleAlsoAsk": also_ask,
    }


def footprint_search(platform: str, geo: str = "Dubai", role: str = "coach",
                     country: str | None = "ae", raw: bool = False) -> dict:
    """Work one platform's Google footprint via BOTH query shapes and merge —
    the Apify-backed path (fetches through `google_search`, which draws on
    the shared monthly USD cap). Prefer `main.py classify-footprint`
    (Firecrawl-fed, `audit/footprint.py`) instead; this stays as a manual
    fallback for when Firecrawl search is unavailable.

    Runs the subdomain query (`site:<domain> <role> <geo>`) and, when the
    platform has one, the footer-signature query (`"powered by <platform>"
    <role> <geo>`, un-site-scoped so custom domains surface), then hands
    both hit lists to `audit.footprint.classify_footprint_hits` for the
    dedupe/noise-filter/tagging — see that module for the merge logic.

    Returns {"platform", "geo", "hits": [...], "subdomain_count",
    "footprint_count", "queries": [...]}. Two apify calls per platform (one
    if it has no marker); at ~$0.002/call the whole platform set is a few
    tenths of a cent.
    """
    key = platform.lower().strip()
    fp = PLATFORM_FOOTPRINTS.get(key)
    if not fp:
        raise ApifyError(
            f"unknown platform {key!r}; known: {', '.join(PLATFORM_FOOTPRINTS)}"
        )

    sub_q = f"{role} {geo}"
    subdomain_hits = google_search(sub_q, site=fp["domain"], country=country)

    marker_hits: list[dict] = []
    if fp["marker"]:
        fp_q = f'"{fp["marker"]}" {role} {geo}'
        marker_hits = google_search(fp_q, country=country)

    return classify_footprint_hits(key, subdomain_hits, marker_hits, geo=geo, role=role)
