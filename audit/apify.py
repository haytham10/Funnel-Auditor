"""
NOTE (2026-07-31): behaviour unchanged by the pivot, wording updated. This file
was written when Firecrawl was the free fetcher and named it throughout;
Firecrawl is gone. "The free tier" below now means `outbound/fetch.py` (local
HTTP) and the agent's own WebSearch/WebFetch. The rule it encodes is unchanged
and still right: spend Apify only on what the free tier genuinely cannot read —
LinkedIn, Instagram, YouTube counts, email verification.

Apify actor integration — the no-login third-party fetch layer.

The free tier hard-refuses LinkedIn and does not do
authenticated Instagram, so the two login-walled platforms that carry the
best SMYKM hook evidence have no fetch path on their own. This module is
that path: read-only public data pulled through vetted Apify actors that
take a username or URL and need no account — exactly what the hard rules
allow (`enrichment and SMYKM hook-finding ... Instagram the same as
LinkedIn`, never logging in or acting as Haytham anywhere).

It also wraps email verification (the `email-check` WARN → verify fallback,
and the confirm-before-CRM step for a found address) and a Google SERP
scraper (sourcing + finding episode / About / profile pages).

Everything web-fetchable (podcasts, YouTube, About pages, blog posts) stays
on the free tier, which is cheaper and already connected. This layer is
deliberately small: the seven Haytham-vetted actors below and nothing
else. Adding actors is surface area and cost, not capability.

Email verification moved off this layer for a few weeks (2026-07-17, after
the free plan's small monthly USD cap kept getting hit) and is back on it
as of 2026-07-18 — the account is now on a paid (STARTER/BRONZE) plan, so
the cap that forced the move no longer applies day-to-day. `_email_verifier`
in `main.py` defaults to `"apify"` again; `audit/email_verifier.py`
(ZeroBounce) stays fully wired as the automatic fallback for whenever a
call would otherwise land on a capped account (`EMAIL_VERIFY_PROVIDER=
zerobounce` to force it). Google-footprint sourcing stays on the free tier
search feeding `audit/footprint.py` (`main.py classify-footprint`) — that
move was never about the cap, the free tier already does the job at no Apify
cost, so there's nothing to restore there; `footprint_search` below
remains a manual fallback.

Every run through this module is now cost-gated (`COST_APPROVAL_THRESHOLD_
USD`, see below) — a paid plan removes the hard monthly wall but not the
reason to look before a run that costs real money.

## The actor set (vetted; do not expand casually)

    ig_profile  apify/instagram-profile-scraper         profile details (followers/bio/latest posts; optional about-account add-on)
    ig_post     apify/instagram-post-scraper            recent posts w/ captions (date-filterable, can skip pinned); single-post detail
    li_posts    harvestapi/linkedin-profile-posts       recent posts w/ text + date (no cookies) — where LinkedIn hooks live
    li_profile  harvestapi/linkedin-profile-scraper     headline/about/experience; optional email-search mode (finds an address)
    yt_channel  apidojo/youtube-channel-information-scraper  channel subscriber count + stats (the audience-floor number the free tier can't read for YT-native coaches)
    email       account56/email-verifier                MillionVerifier-backed address verification
    email_alt   michael.g/email-verifier-validator      fallback verifier, only when `email` errors on an address
    search      apify/google-search-scraper             Google SERP (site:, country, date filters)

    (email_alt added 2026-07-31: account56/email-verifier started returning
    `{"status": "error", "error": "Failed to verify email"}` for every address
    regardless of validity — an actor-side outage, not a per-address signal.
    Haytham named this specific actor as the fallback. `verify_emails` below
    retries only the addresses `email` errored on, and normalizes the result
    (`status`/`technical_status`/`catch_all` -> the `result` token
    `classify_verification` already reads) rather than teaching that function
    a second vocabulary.)

    (yt_channel added 2026-07-19 for the qualifier's audience floor: a coach
    whose only sizeable channel is YouTube (subscriber count is JS/login-walled
    to the free tier) otherwise stalls at "unconfirmed audience." One channel = one
    dataset-item at $0.0005, so a single-lead call clears the gate ~200x over.
    It returns the SUBSCRIBER COUNT, not a latest-upload date — YouTube activity
    recency stays a free scrape of the channel's /videos page, per the
    free-first rule. Handle path via `youtubeHandles`; /channel/UC.. and
    /c/.. URLs via `startUrls`.)

    (Instagram split from the single apify/instagram-scraper into the two
    dedicated actors above 2026-07-18: the unified actor's `details` mode is
    now instagram-profile-scraper and its `posts`/single-post modes are now
    instagram-post-scraper. Both are Apify's own sibling actors — same output
    field names, slightly cheaper per item, and the post actor adds a native
    `skipPinnedPosts` toggle. The unified actor's reels/comments/mentions/
    stories modes had no consumer in the skills and were dropped with it.)

    (li_profile went harvestapi/linkedin-profile-scraper -> apimaestro/
    linkedin-profile-detail 2026-07-16 -> back to harvestapi 2026-07-31, on
    Haytham's call. It now matches li_posts, so both LinkedIn calls run
    through one vendor. **The thing that forced the 2026-07-16 move was a
    ~20-runs/month quota the harvestapi PROFILE actor enforces itself,
    independent of Apify billing, and a batch hit it mid-run.** Nothing in
    this module can see that quota — it is not in `account_limits()`, which
    reads Apify's USD cap and knows nothing about a vendor's own counter, and
    it does not show up in the cost gate either, since a quota-exhausted run
    is cheap, not expensive. So it fails as a mid-batch actor error on run 21,
    the way it did before. If a batch dies on LinkedIn profiles with a quota
    message, that is this, not a code fault: the profile call is optional by
    design (posts-first, below), so drop it for the rest of the run rather
    than swapping actors mid-batch.

    The two actors return DIFFERENT shapes and `linkedin_profile` normalizes
    both to the same record — apimaestro nested everything under `basic_info`
    with an `email` string; harvestapi is flat, splits `firstName`/`lastName`,
    puts the address list under `emails` (each entry carrying its own
    deliverability verdict, which is why the picker below prefers a valid one)
    and the location string under `location.linkedinText`. Callers see the
    same keys either way.)

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

## Cost approval gate

Every wrapper below (`instagram`, `instagram_post`, `linkedin_posts`,
`linkedin_profile`, `youtube_channel`, `verify_emails`, `google_search`) estimates the run's
cost BEFORE calling Apify — its primary charge event's live per-unit price
(read from `GET /v2/acts/<id>`, at this account's actual plan tier) times
the item count the call implies (`resultsLimit`, `maxPosts`,
`len(emails)`, `pages`, ...). If that estimate is missing (pricing
unreadable) or exceeds `COST_APPROVAL_THRESHOLD_USD` ($0.10), the call
raises `ApifyCostApprovalRequired` instead of running — get Haytham's
sign-off, then re-run with `approved=True` (CLI: `--approve-cost`).
Ordinary single-lead calls (one Instagram pull, one address, a 5-post
LinkedIn check) price out to a few cents at most and clear the gate
automatically; a bulk pull or an oversized `--limit` is what actually
trips it. The estimate prices the dominant event only (a run's primary
line item), not situational add-ons (reactions/comments if requested, a
captured AI Overview) — a go/no-go signal, not an invoice.

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
    "ig_profile": "apify~instagram-profile-scraper",
    "ig_post": "apify~instagram-post-scraper",
    "li_posts": "harvestapi~linkedin-profile-posts",
    "li_profile": "harvestapi~linkedin-profile-scraper",
    "yt_channel": "apidojo~youtube-channel-information-scraper",
    "email": "account56~email-verifier",
    "email_alt": "michael.g~email-verifier-validator",
    "search": "apify~google-search-scraper",
}

# Default sync-run ceiling. run-sync-get-dataset-items holds the HTTP
# connection open until the run finishes or this elapses; a run that
# overruns returns 408 and should be re-issued async (run_actor_async).
_SYNC_TIMEOUT_SECS = 240

# A run whose estimated cost is unknown or exceeds this gets blocked with
# ApifyCostApprovalRequired instead of running — see "Cost approval gate"
# above.
COST_APPROVAL_THRESHOLD_USD = 0.10

LI_POSTED_LIMITS = ("any", "1h", "24h", "week", "month", "3months", "6months", "year")

# harvestapi/linkedin-profile-scraper's two modes, as the exact enum strings
# its input schema accepts (the prices are part of the label, not decoration —
# a near-miss string is rejected by the actor). Which one runs decides which
# charge event bills, hence LI_PROFILE_EVENTS below.
LI_PROFILE_MODES = {
    False: "Profile details no email ($4 per 1k)",
    True: "Profile details + email search ($10 per 1k)",
}
# Charge-event keys for the same two modes. This actor flags NEITHER event as
# primary and both are recurring, so the pricing reader can't pick one on its
# own and would return "can't estimate" — which the gate treats as blocked.
# Naming the event is what keeps an ordinary one-profile call automatic, and
# it prices the mode actually being run rather than assuming the cheap one.
LI_PROFILE_EVENTS = {False: "profile", True: "profile_with_email"}

# Only the two modes the dedicated actors cover: details -> profile scraper,
# posts -> post scraper. The old unified actor's reels/comments/mentions/
# stories modes had no consumer and went with it.
IG_RESULT_TYPES = ("posts", "details")


class ApifyError(RuntimeError):
    """Any Apify-side failure: missing token, billing, timeout, bad input."""


class ApifyCostApprovalRequired(ApifyError):
    """Raised instead of running when a call's estimated cost is unknown or
    exceeds COST_APPROVAL_THRESHOLD_USD — the run needs Haytham's sign-off
    before it happens, not after. Carries the estimate so a caller can
    print it and re-run with approved=True (CLI: --approve-cost) once
    that sign-off is given."""

    def __init__(self, actor_id: str, estimated_usd: float | None, reason: str = ""):
        self.actor_id = actor_id
        self.estimated_usd = estimated_usd
        if estimated_usd is None:
            detail = f"cost could not be estimated ({reason})" if reason else "cost could not be estimated"
        else:
            detail = f"estimated cost ${estimated_usd:.3f}"
        super().__init__(
            f"{detail} for {actor_id} — exceeds the ${COST_APPROVAL_THRESHOLD_USD:.2f} "
            "approval threshold. Get Haytham's approval, then re-run with "
            "approved=True (CLI: --approve-cost)."
        )


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

    Added after a batch run (evening prep, Jul 15 2026) burned extra tool
    calls when several per-lead agents each independently discovered a
    dead monthly quota by running actors into it one at a time. (Those
    agents belonged to the funnel-audit pipeline and are gone; the lesson
    transferred to the research workers.) This lets an orchestrator check
    once, up front, and skip Apify
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


# Per-process caches — one lookup per actor / per account per run of the
# CLI, not one per call. Pricing and plan tier don't change mid-process.
# Keyed by (actor_id, event_key) because one actor can bill different events
# at different prices — li_profile's email mode is 2.5x its no-email mode, and
# a cache keyed on the actor alone would price the second call at the first
# call's rate.
_pricing_cache: dict[tuple[str, str | None], float | None] = {}
_tier_cache: dict[str, str | None] = {"tier": None, "fetched": False}


def _account_tier() -> str | None:
    """Current plan tier (e.g. 'BRONZE'), read from `GET /v2/users/me` —
    PAY_PER_EVENT actors price differently per tier and there's no way to
    estimate a run's cost without knowing which column applies. Cached per
    process; returns None on any failure so `_actor_primary_event_price_usd`
    falls back to the FREE-tier (highest) column rather than silently
    under-pricing the estimate."""
    if _tier_cache["fetched"]:
        return _tier_cache["tier"]
    tier = None
    try:
        resp = requests.get(f"{APIFY_BASE}/users/me", headers=_auth_headers(), timeout=20)
        if resp.ok:
            tier = ((resp.json().get("data") or {}).get("plan") or {}).get("tier")
    except requests.RequestException:
        pass
    _tier_cache["tier"] = tier
    _tier_cache["fetched"] = True
    return tier


def _actor_primary_event_price_usd(actor_id: str, event_key: str | None = None) -> float | None:
    """Current per-unit USD price of an actor's dominant charge event, read
    live from `GET /v2/acts/<id>` (the same pricingInfos block shown on the
    actor's Store page) — the actual number Apify will bill, not a
    hardcoded guess that goes stale. Handles the two pricing models the
    vetted actor set uses: flat PRICE_PER_DATASET_ITEM, and PAY_PER_EVENT
    (reads the event flagged `isPrimaryEvent`; if none is flagged — e.g.
    account56/email-verifier doesn't flag one — falls back to the sole
    recurring, non-one-time event when there's exactly one, since that's
    unambiguous; tiered by plan if the event has tiers). Returns None if
    pricing can't be read at all (network failure, actor not found, or a
    pricing model/shape this doesn't recognize) — callers treat None as
    'can't estimate' and require approval rather than assume a run is
    cheap.

    `event_key` names the charge event outright, for an actor that offers
    several and flags none (harvestapi/linkedin-profile-scraper prices
    `profile` and `profile_with_email` and marks neither primary, so the
    inference above gives up on it). A caller that knows which mode it is
    about to run knows which event bills; without the hint that call would be
    unpriceable and blocked forever. A named event that isn't in the actor's
    pricing still returns None — a hint that has gone stale must fail closed,
    not fall back to a different event's price."""
    cache_key = (actor_id, event_key)
    if cache_key in _pricing_cache:
        return _pricing_cache[cache_key]
    price: float | None = None
    try:
        resp = requests.get(f"{APIFY_BASE}/acts/{actor_id}", headers=_auth_headers(), timeout=20)
        if resp.ok:
            infos = (resp.json().get("data") or {}).get("pricingInfos") or []
            if infos:
                current = infos[-1]  # most recent entry — the one in effect now
                model = current.get("pricingModel")
                if model == "PRICE_PER_DATASET_ITEM":
                    price = current.get("pricePerUnitUsd")
                elif model == "PAY_PER_EVENT":
                    events = ((current.get("pricingPerEvent") or {})
                              .get("actorChargeEvents") or {})
                    if event_key is not None:
                        primary = events.get(event_key)
                    else:
                        primary = next((e for e in events.values() if e.get("isPrimaryEvent")), None)
                        if primary is None:
                            recurring = [e for e in events.values() if not e.get("isOneTimeEvent")]
                            if len(recurring) == 1:
                                primary = recurring[0]
                    if primary is not None:
                        tiered = primary.get("eventTieredPricingUsd")
                        if tiered:
                            tier = _account_tier() or "FREE"
                            entry = tiered.get(tier) or tiered.get("FREE")
                            price = entry.get("tieredEventPriceUsd") if entry else None
                        else:
                            price = primary.get("eventPriceUsd")
    except requests.RequestException:
        pass
    _pricing_cache[cache_key] = price
    return price


def estimate_cost_usd(actor_id: str, item_count: int,
                      event_key: str | None = None) -> tuple[float | None, str]:
    """Estimate one run's cost as (primary event's live per-unit price) x
    item_count — item_count being whatever the caller expects Apify to
    charge per-item for (resultsLimit, maxPosts, len(emails), pages, ...).
    Prices the dominant cost driver only, not situational add-ons
    (reactions/comments if requested, a captured AI Overview) — a go/no-go
    estimate for the approval gate, not an invoice. `event_key` names the
    charge event when the actor prices several and flags none as primary; see
    `_actor_primary_event_price_usd`. Returns (None, reason) when the price
    can't be read."""
    price = _actor_primary_event_price_usd(actor_id, event_key)
    if price is None:
        return None, "pricing unavailable (network error or unrecognized pricing model)"
    return round(price * max(item_count, 1), 4), ""


def _require_cost_approval(actor_id: str, item_count: int, approved: bool,
                           event_key: str | None = None) -> None:
    """The approval gate every wrapper below calls before running. No-op
    once approved=True (the caller already has Haytham's sign-off for this
    call); otherwise estimates the cost and raises ApifyCostApprovalRequired
    if it's unknown or over COST_APPROVAL_THRESHOLD_USD."""
    if approved:
        return
    est, reason = estimate_cost_usd(actor_id, item_count, event_key)
    if est is None or est > COST_APPROVAL_THRESHOLD_USD:
        raise ApifyCostApprovalRequired(actor_id, est, reason)


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


def _raise_on_actor_error(items: list[dict], target: str) -> None:
    """Some actors report a per-item failure (bad handle, private/renamed/
    deleted account, rate limit) as an `error`/`errorDescription` field in an
    otherwise-normal dataset item rather than a non-2xx HTTP response —
    `run_actor` has no non-2xx to catch, so that failure sailed through as a
    "successful" empty-ish result. Worse, `_lean()`'s allow-list keeps only
    known-good fields, so `error`/`errorDescription` silently vanished,
    leaving what looked like an empty-but-valid profile instead of a failure
    — the exact shape that read as a routing bug on 2026-07-20 (it wasn't;
    `--mode details` was hitting the right actor the whole time) when it was
    actually the account being unresolvable and the failure being swallowed
    before anyone saw it. Surface it loud and early instead."""
    for item in items:
        if isinstance(item, dict) and item.get("error"):
            desc = item.get("errorDescription", item["error"])
            raise ApifyError(
                f"actor could not resolve {target!r}: {desc} (raw error: {item['error']!r}). "
                "Likely private, renamed, or nonexistent — not a code/routing issue. "
                "Re-run with --raw to see the full actor response."
            )


def _ig_username(url_or_handle: str) -> str:
    """Reduce a profile URL or @handle to the bare username the
    instagram-profile-scraper's `usernames` field wants. A plain handle
    passes through (leading @ stripped); a URL yields its first path
    segment (`https://www.instagram.com/coachjane/?hl=en` → `coachjane`).
    The post scraper takes URLs directly, so this is only used on the
    profile path."""
    s = url_or_handle.strip().strip("@")
    if "instagram.com" in s:
        path = s.split("instagram.com/", 1)[1]
        s = path.split("?", 1)[0].split("/", 1)[0]
    return s.strip("/")


def instagram(url: str, mode: str = "posts", newer_than: str | None = None,
              limit: int = 12, skip_pinned: bool = False, include_about: bool = False,
              raw: bool = False, approved: bool = False) -> list[dict]:
    """Instagram profile enrichment, split across two dedicated actors.

    mode='details' → apify/instagram-profile-scraper: profile metadata
    (followers, bio, latest posts; `include_about` adds the paid
    about-account block — country, join date, verification). Gated as 1
    profile.

    mode='posts' → apify/instagram-post-scraper: recent posts with captions,
    `newer_than` (e.g. '7 days', '2026-07-01') filtering recency,
    `skip_pinned` dropping pinned posts (default off — a pinned post is often
    the coach's signature/framework content, i.e. exactly the SMYKM hook).
    Gated on `limit`.

    Pass approved=True once Haytham has signed off on an estimate over
    COST_APPROVAL_THRESHOLD_USD — see "Cost approval gate" above."""
    if mode not in IG_RESULT_TYPES:
        raise ApifyError(f"instagram mode must be one of {IG_RESULT_TYPES}, got {mode!r}")

    if mode == "details":
        _require_cost_approval(ACTORS["ig_profile"], 1, approved)
        username = _ig_username(url)
        run: dict[str, Any] = {"usernames": [username]}
        if include_about:
            run["includeAboutSection"] = True
        items = run_actor(ACTORS["ig_profile"], run, memory_mbytes=1024)
        if raw:
            return items
        _raise_on_actor_error(items, username)
        keep = ("username", "fullName", "biography", "followersCount",
                "postsCount", "url", "latestPosts", "about")
        return [_lean(i, keep) for i in items]

    # mode == "posts"
    _require_cost_approval(ACTORS["ig_post"], limit, approved)
    run = {"username": [url], "resultsLimit": limit}
    if newer_than:
        run["onlyPostsNewerThan"] = newer_than
    if skip_pinned:
        run["skipPinnedPosts"] = True
    items = run_actor(ACTORS["ig_post"], run, memory_mbytes=1024)
    if raw:
        return items
    _raise_on_actor_error(items, url)
    return [_lean(i, ("ownerUsername", "shortCode", "url", "timestamp", "caption",
                      "likesCount", "commentsCount", "type", "hashtags"))
            for i in items]


def instagram_post(post_url: str, raw: bool = False, approved: bool = False) -> list[dict]:
    """Full detail on one IG post — the deeper dig once a post looks like a
    hook (caption in full plus top comments). Runs apify/instagram-post-scraper
    on the single post URL (its `username` field takes a post URL directly).
    Cost-gated (1 post)."""
    _require_cost_approval(ACTORS["ig_post"], 1, approved)
    items = run_actor(
        ACTORS["ig_post"],
        {"username": [post_url], "resultsLimit": 1},
        memory_mbytes=1024,
    )
    if raw:
        return items
    return [_lean(i, ("ownerUsername", "shortCode", "url", "timestamp", "caption",
                      "likesCount", "commentsCount", "type", "latestComments"))
            for i in items]


def linkedin_posts(url: str, max_posts: int = 5, since: str | None = None,
                   raw: bool = False, approved: bool = False) -> list[dict]:
    """Recent LinkedIn posts (no cookies) — the primary hook source. `since`
    is one of LI_POSTED_LIMITS (e.g. 'week', 'month'). Reactions/comments
    stay off by default to keep the run cheap. Cost-gated on `max_posts`."""
    if since and since not in LI_POSTED_LIMITS:
        raise ApifyError(f"since must be one of {LI_POSTED_LIMITS}, got {since!r}")
    _require_cost_approval(ACTORS["li_posts"], max_posts, approved)
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


def _li_best_email(emails: list) -> str | None:
    """Pick one address out of harvestapi's `emails` list. Each entry carries
    its own `status`/`deliverable` verdict from the actor's own check, so a
    valid one is preferred over a merely-present one; the first address is the
    fallback rather than nothing, since an unverified address still beats no
    address and `email-verify` re-checks it downstream anyway."""
    entries = [e for e in emails or [] if isinstance(e, dict) and e.get("email")]
    if not entries:
        return None
    valid = next(
        (e for e in entries
         if e.get("deliverable") is True or str(e.get("status", "")).lower() == "valid"),
        None,
    )
    return (valid or entries[0])["email"]


def linkedin_profile(url: str, with_email: bool = False, raw: bool = False,
                     approved: bool = False) -> list[dict]:
    """LinkedIn profile enrichment (headline, about, experience). Pass
    with_email=True ONLY when hunting an address for a no-email lead — it
    switches the actor to its email-search mode, which bills 2.5x the plain
    one. Takes a profile URL or bare public identifier. Cost-gated (1 item, at
    the price of whichever mode is being run)."""
    event = LI_PROFILE_EVENTS[bool(with_email)]
    _require_cost_approval(ACTORS["li_profile"], 1, approved, event_key=event)
    items = run_actor(
        ACTORS["li_profile"],
        # `queries` takes profile URLs or bare public identifiers
        # interchangeably, which is the one input field that accepts both —
        # the more specific `urls`/`publicIdentifiers` fields would make the
        # caller decide which of the two it holds.
        {"queries": [url], "profileScraperMode": LI_PROFILE_MODES[bool(with_email)]},
        memory_mbytes=256,
    )
    if raw:
        return items
    _raise_on_actor_error(items, url)
    out = []
    for i in items:
        location = i.get("location") or {}
        current = (i.get("currentPosition") or [{}])[0]
        experience = []
        for e in i.get("experience") or []:
            end = e.get("endDate") or {}
            rec_e = {
                "title": e.get("position"),
                "company": e.get("companyName"),
                "location": e.get("location"),
                "duration": e.get("duration"),
                "description": e.get("description"),
                # harvestapi has no is_current flag; a position still running
                # reads "Present" as its end date, which is the same fact.
                "is_current": str(end.get("text", "")).strip().lower() == "present" or None,
            }
            experience.append({k: v for k, v in rec_e.items() if v not in (None, "", [])})
        websites = [w for w in (i.get("websites") or []) if isinstance(w, str)]
        name = " ".join(p for p in (i.get("firstName"), i.get("lastName")) if p)
        rec = {
            "linkedinUrl": i.get("linkedinUrl"),
            "publicIdentifier": i.get("publicIdentifier"),
            "fullName": name,
            "headline": i.get("headline"),
            "about": i.get("about"),
            "location": location.get("linkedinText"),
            "currentCompany": current.get("companyName"),
            "followerCount": i.get("followerCount"),
            "website": websites[0] if websites else None,
            "email": _li_best_email(i.get("emails")),
            "experience": experience,
        }
        out.append({k: v for k, v in rec.items() if v not in (None, "", [])})
    return out


def _yt_run_input(channel: str) -> dict:
    """Map a YouTube channel URL or @handle to the apidojo actor's input.
    Bare handles and youtube.com/@handle URLs go via `youtubeHandles` (the
    path that reliably resolves a single channel); /channel/UC.., /c/.., and
    /user/.. URLs go via `startUrls`. Always caps at one item."""
    s = channel.strip()
    low = s.lower()
    if any(p in low for p in ("youtube.com/channel/", "youtube.com/c/", "youtube.com/user/")):
        return {"startUrls": [s], "maxItems": 1}
    if "youtube.com/@" in low:
        h = "@" + low.split("youtube.com/@", 1)[1].split("/", 1)[0].split("?", 1)[0]
    elif s.startswith("@"):
        h = s
    elif "youtube.com" in low:
        # some other youtube URL shape — let the actor resolve it as a start URL
        return {"startUrls": [s], "maxItems": 1}
    else:
        h = "@" + s.lstrip("@")
    return {"youtubeHandles": [h], "maxItems": 1}


def youtube_channel(channel: str, raw: bool = False, approved: bool = False) -> list[dict]:
    """YouTube channel info — the subscriber COUNT (the audience-floor number
    the free tier can't read off a JS/login-walled channel page) for a YT-native
    coach. Takes a channel URL or @handle. Returns subscriberCount + basic
    stats; it does NOT return a latest-upload date, so get YouTube activity
    recency from a free scrape of the channel's /videos page instead.
    Cost-gated (1 channel = 1 dataset-item, ~$0.0005)."""
    _require_cost_approval(ACTORS["yt_channel"], 1, approved)
    items = run_actor(ACTORS["yt_channel"], _yt_run_input(channel), memory_mbytes=512)
    if raw:
        return items
    return [_lean(i, ("name", "handle", "url", "subscriberCount", "videoCount",
                      "viewCount", "joinedAt", "description"))
            for i in items]


def _normalize_alt_email_result(item: dict) -> dict:
    """`email_alt` (michael.g/email-verifier-validator) speaks its own
    vocabulary — top-level `status`: good/bad, `technical_status`:
    valid/invalid. Fold it into the `result` token `classify_verification`
    already reads instead of teaching that function a second vocabulary."""
    if item.get("disposable"):
        token = "disposable"
    elif item.get("catch_all"):
        token = "catch_all"
    else:
        technical = (item.get("technical_status") or "").strip().lower()
        token = technical if technical in ("valid", "invalid") else "unknown"
    out = dict(item)
    out["result"] = token
    return out


# account56/email-verifier has been in an outage since 2026-07-31 (returns
# `{"status": "error"}` for every address, valid or not — an actor fault, not
# a per-address signal). Haytham: stop spending calls on it while it's down,
# it's wasting credits for a guaranteed error. `email_alt` is now the one
# actually called; flip this back once account56 is confirmed recovered.
_PRIMARY_EMAIL_ACTOR_DOWN = True


def verify_emails(emails: list[str], raw: bool = False, approved: bool = False) -> list[dict]:
    """Verify one or more addresses. The confirm step before a found/guessed
    address enters the CRM. Cost-gated on len(emails).

    Normally tries `email` (account56/email-verifier, MillionVerifier-backed)
    first and only falls back to `email_alt` (michael.g/email-verifier-
    validator, Haytham-named fallback) for addresses that error. While
    `_PRIMARY_EMAIL_ACTOR_DOWN` is set, `email` is skipped entirely and
    `email_alt` runs directly — no point paying for a guaranteed error."""
    if not emails:
        raise ApifyError("verify_emails needs at least one address")

    if _PRIMARY_EMAIL_ACTOR_DOWN:
        _require_cost_approval(ACTORS["email_alt"], len(emails), approved)
        alt_items = run_actor(ACTORS["email_alt"], {"emails": emails}, memory_mbytes=256)
        by_email = {alt["email"].strip().lower(): _normalize_alt_email_result(alt)
                    for alt in alt_items if isinstance(alt, dict) and alt.get("email")}
    else:
        _require_cost_approval(ACTORS["email"], len(emails), approved)
        items = run_actor(ACTORS["email"], {"emails": emails}, memory_mbytes=256)
        by_email = {(i.get("email") or "").strip().lower(): i
                    for i in items if isinstance(i, dict) and i.get("email")}
        errored = [e for e in emails
                   if (by_email.get(e.strip().lower()) or {}).get("status") == "error"]
        if errored:
            _require_cost_approval(ACTORS["email_alt"], len(errored), approved)
            alt_items = run_actor(ACTORS["email_alt"], {"emails": errored}, memory_mbytes=256)
            for alt in alt_items:
                if isinstance(alt, dict) and alt.get("email"):
                    by_email[alt["email"].strip().lower()] = _normalize_alt_email_result(alt)

    ordered = [by_email[e.strip().lower()] for e in emails if e.strip().lower() in by_email]
    if raw:
        return ordered
    return [_lean(i, ("email", "status", "result", "resultCode", "subStatus",
                      "free", "role", "disposable"))
            for i in ordered]


def google_search(query: str, pages: int = 1, site: str | None = None,
                  country: str | None = "ae", raw: bool = False,
                  meta: bool = False, approved: bool = False) -> list[dict] | dict:
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
    _require_cost_approval(ACTORS["search"], pages, approved)
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
                     country: str | None = "ae", raw: bool = False,
                     approved: bool = False) -> dict:
    """Work one platform's Google footprint via BOTH query shapes and merge —
    the Apify-backed path (fetches through `google_search`, which draws on
    the shared monthly USD cap). Prefer `main.py classify-footprint`
    (free-search-fed, `audit/footprint.py`) instead; this stays as a manual
    fallback for when free search is unavailable.

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
    subdomain_hits = google_search(sub_q, site=fp["domain"], country=country, approved=approved)

    marker_hits: list[dict] = []
    if fp["marker"]:
        fp_q = f'"{fp["marker"]}" {role} {geo}'
        marker_hits = google_search(fp_q, country=country, approved=approved)

    return classify_footprint_hits(key, subdomain_hits, marker_hits, geo=geo, role=role)
