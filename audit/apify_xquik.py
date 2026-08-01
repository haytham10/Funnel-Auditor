"""Bounded, read-only wrappers for Xquik's public X Apify Actors.

This module owns X-specific input validation and route mapping. The shared
HTTP runner and live-price approval gate remain in ``audit.apify``.

Xquik is an independent third-party service. Not affiliated with X Corp.
"Twitter" and "X" are trademarks of X Corp.
"""

from __future__ import annotations

import re
from math import isfinite
from typing import Any
from urllib.parse import urlparse

DEFAULT_MAX_TOTAL_CHARGE_USD = 0.10

X_TWEET_MODES = (
    "legacy",
    "tweet",
    "tweets",
    "search",
    "profileTweets",
    "profileReplies",
    "profileMedia",
    "profileLikes",
    "listTweets",
    "article",
    "replies",
    "quotes",
    "thread",
    "retweeters",
    "favoriters",
)
X_TWEET_OUTPUT_VARIANTS = ("legacy", "rich", "raw")
X_TWEET_OUTPUT_PRESETS = ("nested", "flat")
X_TWEET_FIELD_STYLES = ("legacy", "camelCase", "snake_case")
X_TWEET_QUERY_TYPES = ("Latest", "Top", "Latest + Top")
X_FOLLOWER_RELATIONS = (
    "followers",
    "following",
    "verified_followers",
    "list_members",
    "list_followers",
    "community_members",
)
X_FOLLOWER_OUTPUT_MODES = ("compact", "full", "raw")
X_FOLLOWER_DEDUPE_MODES = ("none", "first", "merge")
X_FOLLOWER_VERIFIED_TYPES = ("blue", "business", "government", "none")

_X_HANDLE_RE = re.compile(r"^[A-Za-z0-9_]{1,15}$")
_X_HOSTS = {
    "x.com",
    "www.x.com",
    "twitter.com",
    "www.twitter.com",
    "mobile.twitter.com",
}
_X_RESERVED_PATHS = {
    "bookmarks",
    "compose",
    "communities",
    "explore",
    "home",
    "i",
    "intent",
    "lists",
    "login",
    "messages",
    "notifications",
    "search",
    "settings",
    "share",
    "signup",
}
_X_TWEET_ID_FIELDS = {
    "tweet": "tweetIds",
    "tweets": "tweetIds",
    "article": "articleTweetIds",
    "replies": "replyTweetIds",
    "quotes": "quoteTweetIds",
    "thread": "threadTweetIds",
    "retweeters": "retweeterTweetIds",
    "favoriters": "favoriterTweetIds",
}
_X_PROFILE_MODES = {
    "profileTweets",
    "profileReplies",
    "profileMedia",
    "profileLikes",
}


def _apify():
    """Load the shared runner lazily to avoid an import cycle."""
    from audit import apify

    return apify


def _error(message: str):
    return _apify().ApifyError(message)


def _choice(name: str, value: str, choices: tuple[str, ...]) -> str:
    if value not in choices:
        raise _error(f"{name} must be one of {choices}, got {value!r}")
    return value


def _x_url(value: str) -> str:
    """Validate one public X URL before forwarding it to an Actor."""
    candidate = value.strip()
    parsed = urlparse(candidate)
    hostname = (parsed.hostname or "").lower()
    if (
        parsed.scheme not in {"http", "https"}
        or hostname not in _X_HOSTS
        or parsed.username
        or parsed.password
    ):
        raise _error("X targets must use an x.com or twitter.com HTTP(S) URL")
    return candidate


def _x_url_parts(value: str) -> list[str]:
    return [part for part in urlparse(_x_url(value)).path.split("/") if part]


def _x_handle(value: str) -> str:
    candidate = value.strip()
    if "://" in candidate:
        parts = _x_url_parts(candidate)
        candidate = parts[0] if parts else ""
    candidate = candidate.lstrip("@")
    if candidate.lower() in _X_RESERVED_PATHS or not _X_HANDLE_RE.fullmatch(candidate):
        raise _error(f"invalid X handle: {value!r}")
    return candidate


def _x_numeric_id(value: str, marker: str) -> str:
    candidate = value.strip()
    if "://" in candidate:
        parts = _x_url_parts(candidate)
        try:
            candidate = parts[parts.index(marker) + 1]
        except (ValueError, IndexError) as exc:
            raise _error(f"X URL does not contain a {marker} ID: {value!r}") from exc
    if not candidate.isdigit():
        raise _error(f"X {marker} ID must be numeric, got {value!r}")
    return candidate


def _tweet_input(
    targets: list[str],
    *,
    mode: str,
    max_items: int,
    max_items_per_target: int | None,
    output_variant: str,
    output_preset: str,
    field_style: str,
    query_type: str,
    include_search_terms: bool,
    include_articles: bool,
    include_original_tweet: bool,
    include_unavailable_fields: bool,
    respect_profile_subpages: bool,
) -> dict[str, Any]:
    if not targets:
        raise _error("x_tweets needs at least one target")
    _choice("mode", mode, X_TWEET_MODES)
    _choice("output_variant", output_variant, X_TWEET_OUTPUT_VARIANTS)
    _choice("output_preset", output_preset, X_TWEET_OUTPUT_PRESETS)
    _choice("field_style", field_style, X_TWEET_FIELD_STYLES)
    _choice("query_type", query_type, X_TWEET_QUERY_TYPES)

    run: dict[str, Any] = {
        "mode": mode,
        "maxItems": max_items,
        "outputVariant": output_variant,
        "outputPreset": output_preset,
        "fieldStyle": field_style,
        "queryType": query_type,
    }
    if max_items_per_target is not None:
        if max_items_per_target <= 0:
            raise _error("max_items_per_target must be greater than zero")
        run["maxItemsPerTarget"] = max_items_per_target
    optional_flags = {
        "includeSearchTerms": include_search_terms,
        "includeArticles": include_articles,
        "includeOriginalTweet": include_original_tweet,
        "includeUnavailableFields": include_unavailable_fields,
        "respectProfileSubpages": respect_profile_subpages,
    }
    run.update({key: True for key, enabled in optional_flags.items() if enabled})

    if mode == "legacy":
        urls = [_x_url(target) for target in targets if "://" in target]
        terms = [target.strip() for target in targets if "://" not in target]
        if urls:
            run["startUrls"] = [{"url": url} for url in urls]
        if terms:
            run["searchTerms"] = terms
        if not urls and not any(terms):
            raise _error("x_tweets needs at least one non-empty target")
    elif mode == "search":
        terms = [target.strip() for target in targets]
        if not all(terms):
            raise _error("search targets must not be empty")
        run["searchTerms"] = terms
    elif mode in _X_PROFILE_MODES:
        run["twitterHandles"] = [_x_handle(target) for target in targets]
    elif mode == "listTweets":
        run["listIds"] = [_x_numeric_id(target, "lists") for target in targets]
    else:
        field = _X_TWEET_ID_FIELDS[mode]
        run[field] = [_x_numeric_id(target, "status") for target in targets]
    return run


def _require_run_approval(
    actor_id: str,
    max_items: int,
    max_total_charge_usd: float,
    approved: bool,
) -> None:
    core = _apify()
    if not 1 <= max_items <= 10000:
        raise core.ApifyError("max_items must be between 1 and 10000")
    if not isfinite(max_total_charge_usd) or max_total_charge_usd <= 0:
        raise core.ApifyError(
            "max_total_charge_usd must be a finite number greater than zero"
        )
    core._require_cost_approval(actor_id, max_items, approved)
    if not approved and max_total_charge_usd > core.COST_APPROVAL_THRESHOLD_USD:
        raise core.ApifyCostApprovalRequired(
            actor_id,
            max_total_charge_usd,
            "requested maximum charge",
        )


def x_tweets(
    targets: list[str],
    *,
    mode: str = "search",
    max_items: int = 25,
    max_items_per_target: int | None = None,
    output_variant: str = "rich",
    output_preset: str = "nested",
    field_style: str = "camelCase",
    query_type: str = "Latest",
    include_search_terms: bool = False,
    include_articles: bool = False,
    include_original_tweet: bool = False,
    include_unavailable_fields: bool = False,
    respect_profile_subpages: bool = False,
    max_total_charge_usd: float = DEFAULT_MAX_TOTAL_CHARGE_USD,
    timeout_secs: int = 240,
    approved: bool = False,
) -> list[dict]:
    """Collect public X posts through Xquik's X Tweet Scraper."""
    run = _tweet_input(
        targets,
        mode=mode,
        max_items=max_items,
        max_items_per_target=max_items_per_target,
        output_variant=output_variant,
        output_preset=output_preset,
        field_style=field_style,
        query_type=query_type,
        include_search_terms=include_search_terms,
        include_articles=include_articles,
        include_original_tweet=include_original_tweet,
        include_unavailable_fields=include_unavailable_fields,
        respect_profile_subpages=respect_profile_subpages,
    )
    core = _apify()
    actor_id = core.ACTORS["x_tweets"]
    _require_run_approval(
        actor_id,
        max_items,
        max_total_charge_usd,
        approved,
    )
    return core.run_actor(
        actor_id,
        run,
        timeout_secs=timeout_secs,
        max_items=max_items,
        max_total_charge_usd=max_total_charge_usd,
    )


def _follower_target_field(
    relations: list[str],
    target_type: str,
) -> tuple[str, str]:
    if target_type == "user_ids":
        profile_relations = {"followers", "following", "verified_followers"}
        if any(relation not in profile_relations for relation in relations):
            raise _error("user_ids only support profile relations")
        return "userIds", "user"
    if target_type != "auto":
        raise _error("target_type must be 'auto' or 'user_ids'")

    categories = {
        "list"
        if relation in {"list_members", "list_followers"}
        else "community"
        if relation == "community_members"
        else "profile"
        for relation in relations
    }
    if len(categories) != 1:
        raise _error(
            "bare targets cannot mix profile, list, and community relations; "
            "use relation URLs instead"
        )
    category = categories.pop()
    if category == "list":
        return "listIds", "lists"
    if category == "community":
        return "communityIds", "communities"
    return "twitterHandles", "handle"


def _validate_ranges(filters: dict[str, int | None]) -> None:
    for name, value in filters.items():
        if value is not None and value < 0:
            raise _error(f"{name} must not be negative")
    for minimum, maximum in (
        ("minFollowers", "maxFollowers"),
        ("minFollowing", "maxFollowing"),
        ("minStatuses", "maxStatuses"),
    ):
        low = filters[minimum]
        high = filters[maximum]
        if low is not None and high is not None and low > high:
            raise _error(f"{minimum} must not exceed {maximum}")


def x_followers(
    targets: list[str],
    *,
    relation: str = "followers",
    relations: list[str] | None = None,
    target_type: str = "auto",
    max_items: int = 25,
    max_items_per_target: int | None = None,
    output_mode: str = "compact",
    include_unavailable_fields: bool = False,
    include_unavailable_users: bool = False,
    include_target_metadata: bool = True,
    dedupe_across_targets: bool = False,
    dedupe_mode: str = "none",
    overlap_mode: bool = False,
    min_followers: int | None = None,
    max_followers: int | None = None,
    min_following: int | None = None,
    max_following: int | None = None,
    min_statuses: int | None = None,
    max_statuses: int | None = None,
    min_account_age_days: int | None = None,
    verified_only: bool = False,
    verified_type: str | None = None,
    has_website: bool = False,
    has_location: bool = False,
    bio_contains: str | None = None,
    location_contains: str | None = None,
    username_contains: str | None = None,
    max_total_charge_usd: float = DEFAULT_MAX_TOTAL_CHARGE_USD,
    timeout_secs: int = 240,
    approved: bool = False,
) -> list[dict]:
    """Collect public X profile relations through Xquik's Follower Scraper."""
    if not targets:
        raise _error("x_followers needs at least one target")
    selected_relations = relations or [relation]
    for selected in selected_relations:
        _choice("relation", selected, X_FOLLOWER_RELATIONS)
    _choice("output_mode", output_mode, X_FOLLOWER_OUTPUT_MODES)
    _choice("dedupe_mode", dedupe_mode, X_FOLLOWER_DEDUPE_MODES)
    if verified_type is not None:
        _choice("verified_type", verified_type, X_FOLLOWER_VERIFIED_TYPES)

    numeric_filters = {
        "minFollowers": min_followers,
        "maxFollowers": max_followers,
        "minFollowing": min_following,
        "maxFollowing": max_following,
        "minStatuses": min_statuses,
        "maxStatuses": max_statuses,
        "minAccountAgeDays": min_account_age_days,
    }
    _validate_ranges(numeric_filters)

    run: dict[str, Any] = {
        "maxItems": max_items,
        "outputMode": output_mode,
        "includeTargetMetadata": include_target_metadata,
        "dedupeMode": dedupe_mode,
    }
    if len(selected_relations) == 1:
        run["relation"] = selected_relations[0]
    else:
        run["relations"] = selected_relations
    if max_items_per_target is not None:
        if max_items_per_target <= 0:
            raise _error("max_items_per_target must be greater than zero")
        run["maxItemsPerTarget"] = max_items_per_target

    urls = [_x_url(target) for target in targets if "://" in target]
    bare_targets = [target for target in targets if "://" not in target]
    if urls:
        run["startUrls"] = [{"url": url} for url in urls]
    if bare_targets:
        field, kind = _follower_target_field(selected_relations, target_type)
        if kind == "handle":
            run[field] = [_x_handle(target) for target in bare_targets]
        elif kind == "user":
            run[field] = [_x_numeric_id(target, "user") for target in bare_targets]
        else:
            run[field] = [_x_numeric_id(target, kind) for target in bare_targets]

    boolean_fields = {
        "includeUnavailableFields": include_unavailable_fields,
        "includeUnavailableUsers": include_unavailable_users,
        "dedupeAcrossTargets": dedupe_across_targets,
        "overlapMode": overlap_mode,
        "verifiedOnly": verified_only,
        "hasWebsite": has_website,
        "hasLocation": has_location,
    }
    run.update({key: True for key, enabled in boolean_fields.items() if enabled})
    optional_fields: dict[str, Any] = {
        **numeric_filters,
        "verifiedType": verified_type,
        "bioContains": bio_contains,
        "locationContains": location_contains,
        "usernameContains": username_contains,
    }
    run.update(
        {key: value for key, value in optional_fields.items() if value is not None}
    )

    core = _apify()
    actor_id = core.ACTORS["x_followers"]
    _require_run_approval(
        actor_id,
        max_items,
        max_total_charge_usd,
        approved,
    )
    return core.run_actor(
        actor_id,
        run,
        timeout_secs=timeout_secs,
        max_items=max_items,
        max_total_charge_usd=max_total_charge_usd,
    )
