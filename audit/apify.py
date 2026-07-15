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

## The actor set (vetted; do not expand casually)

    ig          apify/instagram-scraper                 profile details + recent posts w/ captions (date-filterable); post detail
    li_posts    harvestapi/linkedin-profile-posts       recent posts w/ text + date (no cookies) — where LinkedIn hooks live
    li_profile  harvestapi/linkedin-profile-scraper     headline/about/experience; optional email-search mode (finds an address)
    email       account56/email-verifier                MillionVerifier-backed address verification
    search      apify/google-search-scraper             Google SERP (site:, country, date filters)

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

APIFY_BASE = "https://api.apify.com/v2"

# Haytham-vetted actors, addressed in the `username~actor-name` form the
# REST API uses. Keep this map tight.
ACTORS = {
    "ig": "apify~instagram-scraper",
    "li_posts": "harvestapi~linkedin-profile-posts",
    "li_profile": "harvestapi~linkedin-profile-scraper",
    "email": "account56~email-verifier",
    "search": "apify~google-search-scraper",
}

# Default sync-run ceiling. run-sync-get-dataset-items holds the HTTP
# connection open until the run finishes or this elapses; a run that
# overruns returns 408 and should be re-issued async (run_actor_async).
_SYNC_TIMEOUT_SECS = 240

LI_POSTED_LIMITS = ("any", "1h", "24h", "week", "month", "3months", "6months", "year")
IG_RESULT_TYPES = ("posts", "details", "comments", "reels", "mentions", "stories")
LI_PROFILE_MODE_NO_EMAIL = "Profile details no email ($4 per 1k)"
LI_PROFILE_MODE_EMAIL = "Profile details + email search ($10 per 1k)"


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
    with_email=True ONLY when hunting an address for a no-email lead — that
    mode costs more ($10/1k vs $4/1k)."""
    run = {
        "queries": [url],
        "profileScraperMode": LI_PROFILE_MODE_EMAIL if with_email else LI_PROFILE_MODE_NO_EMAIL,
    }
    items = run_actor(ACTORS["li_profile"], run, memory_mbytes=256)
    if raw:
        return items
    return [_lean(i, ("linkedinUrl", "publicIdentifier", "firstName", "lastName",
                      "headline", "about", "summary", "location", "email",
                      "emails", "experience", "currentPosition"))
            for i in items]


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
                  country: str | None = "ae", raw: bool = False) -> list[dict]:
    """Google SERP for one query. `site` scopes to a domain (e.g.
    linkedin.com), `country` biases results (default UAE)."""
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
    for page in items:
        for r in page.get("organicResults", []) if isinstance(page, dict) else []:
            hits.append(_lean(r, ("title", "url", "displayedUrl", "description")))
    return hits or items
