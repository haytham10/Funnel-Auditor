"""Offline contract tests for the Xquik Apify Actor routes."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audit import apify


class _FakeResponse:
    ok = True
    status_code = 200

    def json(self):
        return []


def test_run_actor_forwards_server_side_limits(monkeypatch):
    seen = {}

    def fake_post(url, **kwargs):
        seen["url"] = url
        seen.update(kwargs)
        return _FakeResponse()

    monkeypatch.setattr(
        apify,
        "_auth_headers",
        lambda: {"Authorization": "Bearer test"},
    )
    monkeypatch.setattr(apify.requests, "post", fake_post)
    assert (
        apify.run_actor(
            "xquik~x-tweet-scraper",
            {"searchTerms": ["AI"], "maxItems": 5},
            max_items=5,
            max_total_charge_usd=0.10,
        )
        == []
    )
    assert seen["params"]["maxItems"] == 5
    assert seen["params"]["maxTotalChargeUsd"] == 0.10
    assert "token=" not in seen["url"]


def test_x_tweets_routes_every_supported_mode(monkeypatch):
    calls = []

    def fake_run(actor_id, run_input, **kwargs):
        calls.append((actor_id, run_input, kwargs))
        return []

    monkeypatch.setattr(apify, "run_actor", fake_run)
    cases = {
        "legacy": ("https://x.com/OpenAI/status/123", "startUrls"),
        "tweet": ("123", "tweetIds"),
        "tweets": ("123", "tweetIds"),
        "search": ("from:OpenAI API", "searchTerms"),
        "profileTweets": ("@OpenAI", "twitterHandles"),
        "profileReplies": ("@OpenAI", "twitterHandles"),
        "profileMedia": ("@OpenAI", "twitterHandles"),
        "profileLikes": ("@OpenAI", "twitterHandles"),
        "listTweets": ("456", "listIds"),
        "article": ("123", "articleTweetIds"),
        "replies": ("123", "replyTweetIds"),
        "quotes": ("123", "quoteTweetIds"),
        "thread": ("123", "threadTweetIds"),
        "retweeters": ("123", "retweeterTweetIds"),
        "favoriters": ("123", "favoriterTweetIds"),
    }
    for mode, (target, field) in cases.items():
        apify.x_tweets(
            [target],
            mode=mode,
            max_items=5,
            max_total_charge_usd=0.10,
            approved=True,
        )
        actor_id, run_input, kwargs = calls[-1]
        assert actor_id == apify.ACTORS["x_tweets"]
        assert field in run_input
        assert run_input["mode"] == mode
        assert run_input["maxItems"] == 5
        assert kwargs["max_total_charge_usd"] == 0.10


def test_x_followers_routes_relations_and_filters(monkeypatch):
    calls = []

    def fake_run(actor_id, run_input, **kwargs):
        calls.append((actor_id, run_input, kwargs))
        return []

    monkeypatch.setattr(apify, "run_actor", fake_run)
    cases = {
        "followers": ("OpenAI", "twitterHandles"),
        "following": ("OpenAI", "twitterHandles"),
        "verified_followers": ("OpenAI", "twitterHandles"),
        "list_members": ("456", "listIds"),
        "list_followers": ("456", "listIds"),
        "community_members": ("789", "communityIds"),
    }
    for relation, (target, field) in cases.items():
        apify.x_followers(
            [target],
            relation=relation,
            max_items=5,
            min_followers=1000,
            verified_only=True,
            max_total_charge_usd=0.10,
            approved=True,
        )
        actor_id, run_input, kwargs = calls[-1]
        assert actor_id == apify.ACTORS["x_followers"]
        assert field in run_input
        assert run_input["relation"] == relation
        assert run_input["minFollowers"] == 1000
        assert run_input["verifiedOnly"] is True
        assert run_input["includeTargetMetadata"] is True
        assert kwargs["max_total_charge_usd"] == 0.10


def test_x_actor_high_charge_cap_requires_approval(monkeypatch):
    monkeypatch.setattr(
        apify,
        "_actor_primary_event_price_usd",
        lambda actor_id: 0.001,
    )

    def fail_if_run(*args, **kwargs):
        raise AssertionError("run_actor must not run before approval")

    monkeypatch.setattr(apify, "run_actor", fail_if_run)
    try:
        apify.x_tweets(
            ["AI"],
            max_items=5,
            max_total_charge_usd=0.50,
        )
    except apify.ApifyCostApprovalRequired as exc:
        assert exc.actor_id == apify.ACTORS["x_tweets"]
    else:
        raise AssertionError("expected ApifyCostApprovalRequired")


def test_x_actor_rejects_non_x_urls_before_run(monkeypatch):
    def fail_if_run(*args, **kwargs):
        raise AssertionError("run_actor must not receive an invalid URL")

    monkeypatch.setattr(apify, "run_actor", fail_if_run)
    try:
        apify.x_followers(
            ["https://example.com/OpenAI/followers"],
            approved=True,
        )
    except apify.ApifyError as exc:
        assert "x.com or twitter.com" in str(exc)
    else:
        raise AssertionError("expected ApifyError")


def test_x_actor_rejects_non_native_targets_and_charge_caps(monkeypatch):
    def fail_if_run(*args, **kwargs):
        raise AssertionError("run_actor must not receive invalid input")

    monkeypatch.setattr(apify, "run_actor", fail_if_run)
    invalid_calls = (
        lambda: apify.x_tweets(
            ["handle_is_longer_than_15"],
            mode="profileTweets",
            approved=True,
        ),
        lambda: apify.x_tweets(
            ["https://api.x.com/OpenAI/status/123"],
            mode="legacy",
            approved=True,
        ),
        lambda: apify.x_tweets(
            ["AI"],
            max_total_charge_usd=float("nan"),
            approved=True,
        ),
    )
    for invalid_call in invalid_calls:
        try:
            invalid_call()
        except apify.ApifyError:
            pass
        else:
            raise AssertionError("expected ApifyError")


def test_x_follower_filter_ranges_fail_before_run(monkeypatch):
    def fail_if_run(*args, **kwargs):
        raise AssertionError("run_actor must not receive invalid filters")

    monkeypatch.setattr(apify, "run_actor", fail_if_run)
    try:
        apify.x_followers(
            ["OpenAI"],
            min_followers=100,
            max_followers=10,
            approved=True,
        )
    except apify.ApifyError as exc:
        assert "minFollowers must not exceed maxFollowers" in str(exc)
    else:
        raise AssertionError("expected ApifyError")
