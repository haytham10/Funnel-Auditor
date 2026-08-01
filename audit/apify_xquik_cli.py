"""CLI registration and dispatch for the opt-in Xquik Apify routes."""

from __future__ import annotations

from typing import Any

from audit.apify_xquik import (
    X_FOLLOWER_DEDUPE_MODES,
    X_FOLLOWER_OUTPUT_MODES,
    X_FOLLOWER_RELATIONS,
    X_FOLLOWER_VERIFIED_TYPES,
    X_TWEET_FIELD_STYLES,
    X_TWEET_MODES,
    X_TWEET_OUTPUT_PRESETS,
    X_TWEET_OUTPUT_VARIANTS,
    X_TWEET_QUERY_TYPES,
)

COMMANDS = {"x-tweets", "x-followers"}


def run_command(apify: Any, args: Any, approved: bool) -> list[dict]:
    """Dispatch one parsed Xquik command to its bounded wrapper."""
    if args.apify_command == "x-tweets":
        return apify.x_tweets(
            args.targets,
            mode=args.mode,
            max_items=args.max_items,
            max_items_per_target=args.max_items_per_target,
            output_variant=args.output_variant,
            output_preset=args.output_preset,
            field_style=args.field_style,
            query_type=args.query_type,
            include_search_terms=args.include_search_terms,
            include_articles=args.include_articles,
            include_original_tweet=args.include_original_tweet,
            include_unavailable_fields=args.include_unavailable_fields,
            respect_profile_subpages=args.respect_profile_subpages,
            max_total_charge_usd=args.max_charge,
            timeout_secs=args.timeout,
            approved=approved,
        )

    return apify.x_followers(
        args.targets,
        relation=args.relation,
        relations=args.relations,
        target_type=args.target_type,
        max_items=args.max_items,
        max_items_per_target=args.max_items_per_target,
        output_mode=args.output_mode,
        include_unavailable_fields=args.include_unavailable_fields,
        include_unavailable_users=args.include_unavailable_users,
        dedupe_across_targets=args.dedupe_across_targets,
        dedupe_mode=args.dedupe_mode,
        overlap_mode=args.overlap_mode,
        min_followers=args.min_followers,
        max_followers=args.max_followers,
        min_following=args.min_following,
        max_following=args.max_following,
        min_statuses=args.min_statuses,
        max_statuses=args.max_statuses,
        min_account_age_days=args.min_account_age_days,
        verified_only=args.verified_only,
        verified_type=args.verified_type,
        has_website=args.has_website,
        has_location=args.has_location,
        bio_contains=args.bio_contains,
        location_contains=args.location_contains,
        username_contains=args.username_contains,
        max_total_charge_usd=args.max_charge,
        timeout_secs=args.timeout,
        approved=approved,
    )


def _add_common_limits(parser: Any) -> None:
    parser.add_argument(
        "--max",
        dest="max_items",
        type=int,
        default=25,
        help="native Actor item cap, 1 to 10000 (default 25)",
    )
    parser.add_argument(
        "--max-per-target",
        dest="max_items_per_target",
        type=int,
        help="optional item cap for each target",
    )
    parser.add_argument(
        "--max-charge",
        type=float,
        default=0.10,
        help="Apify server-side charge cap in USD (default 0.10)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=240,
        help="sync run timeout in seconds (default 240)",
    )
    parser.add_argument(
        "--approve-cost",
        action="store_true",
        help="Haytham approved the estimate and requested charge cap",
    )


def add_subparsers(apify_sub: Any) -> None:
    """Register both Xquik commands on the existing Apify subparser."""
    tweets = apify_sub.add_parser(
        "x-tweets",
        help="explicit Xquik Actor route for public X posts and conversations",
    )
    tweets.add_argument(
        "targets",
        nargs="+",
        help="queries, handles, IDs, or X URLs matching --mode",
    )
    tweets.add_argument("--mode", default="search", choices=X_TWEET_MODES)
    tweets.add_argument(
        "--output-variant",
        default="rich",
        choices=X_TWEET_OUTPUT_VARIANTS,
    )
    tweets.add_argument(
        "--output-preset",
        default="nested",
        choices=X_TWEET_OUTPUT_PRESETS,
    )
    tweets.add_argument(
        "--field-style",
        default="camelCase",
        choices=X_TWEET_FIELD_STYLES,
    )
    tweets.add_argument(
        "--query-type",
        default="Latest",
        choices=X_TWEET_QUERY_TYPES,
    )
    tweets.add_argument("--include-search-terms", action="store_true")
    tweets.add_argument("--include-articles", action="store_true")
    tweets.add_argument("--include-original-tweet", action="store_true")
    tweets.add_argument("--include-unavailable-fields", action="store_true")
    tweets.add_argument("--respect-profile-subpages", action="store_true")
    _add_common_limits(tweets)

    followers = apify_sub.add_parser(
        "x-followers",
        help="explicit Xquik Actor route for public X profile relations",
    )
    followers.add_argument(
        "targets",
        nargs="+",
        help="handles, numeric IDs, or X relation URLs",
    )
    followers.add_argument(
        "--relation",
        default="followers",
        choices=X_FOLLOWER_RELATIONS,
    )
    followers.add_argument(
        "--relations",
        nargs="+",
        choices=X_FOLLOWER_RELATIONS,
        help="run several compatible relations for the same targets",
    )
    followers.add_argument(
        "--target-type",
        default="auto",
        choices=["auto", "user_ids"],
        help="interpret bare profile targets as handles or numeric user IDs",
    )
    followers.add_argument(
        "--output-mode",
        default="compact",
        choices=X_FOLLOWER_OUTPUT_MODES,
    )
    followers.add_argument("--include-unavailable-fields", action="store_true")
    followers.add_argument("--include-unavailable-users", action="store_true")
    followers.add_argument("--dedupe-across-targets", action="store_true")
    followers.add_argument(
        "--dedupe-mode",
        default="none",
        choices=X_FOLLOWER_DEDUPE_MODES,
    )
    followers.add_argument("--overlap-mode", action="store_true")
    followers.add_argument("--min-followers", type=int)
    followers.add_argument("--max-followers", type=int)
    followers.add_argument("--min-following", type=int)
    followers.add_argument("--max-following", type=int)
    followers.add_argument("--min-statuses", type=int)
    followers.add_argument("--max-statuses", type=int)
    followers.add_argument("--min-account-age-days", type=int)
    followers.add_argument("--verified-only", action="store_true")
    followers.add_argument(
        "--verified-type",
        choices=X_FOLLOWER_VERIFIED_TYPES,
    )
    followers.add_argument("--has-website", action="store_true")
    followers.add_argument("--has-location", action="store_true")
    followers.add_argument("--bio-contains")
    followers.add_argument("--location-contains")
    followers.add_argument("--username-contains")
    _add_common_limits(followers)
