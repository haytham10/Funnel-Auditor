"""Tests for the Apify cost-approval gate added 2026-07-18, alongside
restoring Apify as the default email verifier now that the account is on
a paid (STARTER/BRONZE) plan.

Every actor call in `audit/apify.py` estimates its cost first (the live
per-unit price of the actor's dominant charge event, read from
`GET /v2/acts/<id>`, times the item count the call implies) and raises
`ApifyCostApprovalRequired` instead of running when that estimate is
unknown or exceeds `COST_APPROVAL_THRESHOLD_USD`. These tests exercise the
pure estimation/gate logic against a stubbed `requests.get` — no real
network call, no real spend.

Run: python -m pytest tests/test_apify_cost_gate.py -q
     (or plain `python tests/test_apify_cost_gate.py` for the no-pytest path)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audit import apify


class _FakeResponse:
    def __init__(self, payload, ok=True, status_code=200):
        self._payload = payload
        self.ok = ok
        self.status_code = status_code

    def json(self):
        return self._payload


def _reset_caches():
    apify._pricing_cache.clear()
    apify._tier_cache["tier"] = None
    apify._tier_cache["fetched"] = False


def _tiered_pricing_info(event_name="result", tier_prices=None, is_primary=True):
    tier_prices = tier_prices or {"BRONZE": 0.0023, "FREE": 0.0045}
    return {
        "pricingModel": "PAY_PER_EVENT",
        "pricingPerEvent": {
            "actorChargeEvents": {
                "actor-start": {"isOneTimeEvent": True, "eventPriceUsd": 0.001},
                event_name: {
                    "isPrimaryEvent": is_primary,
                    "eventTieredPricingUsd": {
                        tier: {"tieredEventPriceUsd": price}
                        for tier, price in tier_prices.items()
                    },
                },
            }
        },
    }


# --- _account_tier ------------------------------------------------------------

def test_account_tier_reads_plan_tier(monkeypatch):
    _reset_caches()
    monkeypatch.setattr(apify, "_auth_headers", lambda: {})
    monkeypatch.setattr(
        apify.requests, "get",
        lambda *a, **k: _FakeResponse({"data": {"plan": {"tier": "BRONZE"}}}),
    )
    assert apify._account_tier() == "BRONZE"


def test_account_tier_none_on_network_failure(monkeypatch):
    _reset_caches()
    monkeypatch.setattr(apify, "_auth_headers", lambda: {})

    def raise_it(*a, **k):
        raise apify.requests.RequestException("down")
    monkeypatch.setattr(apify.requests, "get", raise_it)
    assert apify._account_tier() is None


# --- _actor_primary_event_price_usd -------------------------------------------

def test_price_per_dataset_item_model(monkeypatch):
    _reset_caches()
    monkeypatch.setattr(apify, "_auth_headers", lambda: {})
    monkeypatch.setattr(
        apify.requests, "get",
        lambda *a, **k: _FakeResponse(
            {"data": {"pricingInfos": [
                {"pricingModel": "PRICE_PER_DATASET_ITEM", "pricePerUnitUsd": 0.005},
            ]}}
        ),
    )
    assert apify._actor_primary_event_price_usd("some~actor") == 0.005


def test_pay_per_event_uses_flagged_primary_and_account_tier(monkeypatch):
    _reset_caches()
    monkeypatch.setattr(apify, "_auth_headers", lambda: {})

    def fake_get(url, **k):
        if url.endswith("/users/me"):
            return _FakeResponse({"data": {"plan": {"tier": "BRONZE"}}})
        return _FakeResponse({"data": {"pricingInfos": [_tiered_pricing_info()]}})
    monkeypatch.setattr(apify.requests, "get", fake_get)
    assert apify._actor_primary_event_price_usd("apify~instagram-post-scraper") == 0.0023


def test_pay_per_event_falls_back_to_free_tier_when_tier_unknown(monkeypatch):
    _reset_caches()
    monkeypatch.setattr(apify, "_auth_headers", lambda: {})

    def fake_get(url, **k):
        if url.endswith("/users/me"):
            raise apify.requests.RequestException("down")
        return _FakeResponse({"data": {"pricingInfos": [_tiered_pricing_info()]}})
    monkeypatch.setattr(apify.requests, "get", fake_get)
    assert apify._actor_primary_event_price_usd("apify~instagram-post-scraper") == 0.0045


def test_pay_per_event_falls_back_to_sole_recurring_event_when_none_flagged_primary(monkeypatch):
    # account56/email-verifier's real pricing shape: no event is flagged
    # isPrimaryEvent, but only one is recurring (email-verified) —
    # actor-start is a one-time flat fee, so it's unambiguous which one bills
    # per item.
    _reset_caches()
    monkeypatch.setattr(apify, "_auth_headers", lambda: {})
    monkeypatch.setattr(
        apify.requests, "get",
        lambda *a, **k: _FakeResponse({"data": {"pricingInfos": [{
            "pricingModel": "PAY_PER_EVENT",
            "pricingPerEvent": {"actorChargeEvents": {
                "apify-actor-start": {"isOneTimeEvent": True, "eventPriceUsd": 0.0001},
                "email-verified": {"eventPriceUsd": 0.001},
            }},
        }]}}),
    )
    assert apify._actor_primary_event_price_usd("account56~email-verifier") == 0.001


def test_pay_per_event_ambiguous_multiple_recurring_no_primary_flag_is_none(monkeypatch):
    _reset_caches()
    monkeypatch.setattr(apify, "_auth_headers", lambda: {})
    monkeypatch.setattr(
        apify.requests, "get",
        lambda *a, **k: _FakeResponse({"data": {"pricingInfos": [{
            "pricingModel": "PAY_PER_EVENT",
            "pricingPerEvent": {"actorChargeEvents": {
                "post": {"eventPriceUsd": 0.002},
                "reaction": {"eventPriceUsd": 0.002},
            }},
        }]}}),
    )
    assert apify._actor_primary_event_price_usd("ambiguous~actor") is None


def _li_profile_pricing():
    """harvestapi/linkedin-profile-scraper's real pricing shape (2026-07-31):
    two recurring events, NEITHER flagged primary."""
    return {"data": {"pricingInfos": [{
        "pricingModel": "PAY_PER_EVENT",
        "pricingPerEvent": {"actorChargeEvents": {
            "profile": {"eventPriceUsd": 0.004},
            "profile_with_email": {"eventPriceUsd": 0.01},
        }},
    }]}}


def test_named_event_key_prices_ambiguous_actor(monkeypatch):
    # Without the hint this is the ambiguous case above and returns None,
    # which the gate treats as blocked — naming the event is what keeps an
    # ordinary one-profile call automatic.
    _reset_caches()
    monkeypatch.setattr(apify, "_auth_headers", lambda: {})
    monkeypatch.setattr(apify.requests, "get", lambda *a, **k: _FakeResponse(_li_profile_pricing()))
    actor = apify.ACTORS["li_profile"]
    assert apify._actor_primary_event_price_usd(actor) is None
    assert apify._actor_primary_event_price_usd(actor, "profile") == 0.004
    assert apify._actor_primary_event_price_usd(actor, "profile_with_email") == 0.01


def test_unknown_event_key_is_none_not_a_fallback_price(monkeypatch):
    # A hint that has gone stale (actor renamed its events) must fail closed
    # into "can't estimate", never quietly bill at some other event's rate.
    _reset_caches()
    monkeypatch.setattr(apify, "_auth_headers", lambda: {})
    monkeypatch.setattr(apify.requests, "get", lambda *a, **k: _FakeResponse(_li_profile_pricing()))
    assert apify._actor_primary_event_price_usd(apify.ACTORS["li_profile"], "gone") is None


def test_pricing_cache_is_keyed_per_event_not_per_actor(monkeypatch):
    # One actor, two prices: a cache keyed on the actor alone would hand the
    # email mode the no-email mode's price.
    _reset_caches()
    monkeypatch.setattr(apify, "_auth_headers", lambda: {})
    calls = {"n": 0}

    def fake_get(*a, **k):
        calls["n"] += 1
        return _FakeResponse(_li_profile_pricing())
    monkeypatch.setattr(apify.requests, "get", fake_get)
    actor = apify.ACTORS["li_profile"]
    assert apify._actor_primary_event_price_usd(actor, "profile") == 0.004
    assert apify._actor_primary_event_price_usd(actor, "profile_with_email") == 0.01
    assert apify._actor_primary_event_price_usd(actor, "profile") == 0.004  # cached
    assert calls["n"] == 2


def test_price_none_on_network_failure(monkeypatch):
    _reset_caches()
    monkeypatch.setattr(apify, "_auth_headers", lambda: {})

    def raise_it(*a, **k):
        raise apify.requests.RequestException("down")
    monkeypatch.setattr(apify.requests, "get", raise_it)
    assert apify._actor_primary_event_price_usd("some~actor") is None


def test_price_cached_after_first_lookup(monkeypatch):
    _reset_caches()
    monkeypatch.setattr(apify, "_auth_headers", lambda: {})
    calls = {"n": 0}

    def fake_get(*a, **k):
        calls["n"] += 1
        return _FakeResponse(
            {"data": {"pricingInfos": [
                {"pricingModel": "PRICE_PER_DATASET_ITEM", "pricePerUnitUsd": 0.005},
            ]}}
        )
    monkeypatch.setattr(apify.requests, "get", fake_get)
    apify._actor_primary_event_price_usd("cached~actor")
    apify._actor_primary_event_price_usd("cached~actor")
    assert calls["n"] == 1


# --- estimate_cost_usd / _require_cost_approval -------------------------------

def test_estimate_cost_multiplies_price_by_item_count(monkeypatch):
    _reset_caches()
    monkeypatch.setattr(
        apify, "_actor_primary_event_price_usd", lambda actor_id, event_key=None: 0.002
    )
    est, reason = apify.estimate_cost_usd("some~actor", 10)
    assert est == 0.02
    assert reason == ""


def test_estimate_cost_unknown_when_price_unavailable(monkeypatch):
    _reset_caches()
    monkeypatch.setattr(apify, "_actor_primary_event_price_usd", lambda actor_id, event_key=None: None)
    est, reason = apify.estimate_cost_usd("some~actor", 10)
    assert est is None
    assert reason


def test_require_cost_approval_noop_when_already_approved(monkeypatch):
    _reset_caches()
    # If this were called, it would fail the test (no price mock supplied) —
    # approved=True must short-circuit before any estimate is attempted.
    def boom(actor_id, event_key=None):
        raise AssertionError("should not estimate when already approved")
    monkeypatch.setattr(apify, "_actor_primary_event_price_usd", boom)
    apify._require_cost_approval("some~actor", 999, approved=True)  # no raise


def test_require_cost_approval_blocks_over_threshold(monkeypatch):
    _reset_caches()
    monkeypatch.setattr(apify, "_actor_primary_event_price_usd", lambda actor_id, event_key=None: 0.002)
    try:
        apify._require_cost_approval("some~actor", 100, approved=False)  # $0.20
    except apify.ApifyCostApprovalRequired as exc:
        assert exc.estimated_usd == 0.2
        assert exc.actor_id == "some~actor"
    else:
        raise AssertionError("expected ApifyCostApprovalRequired")


def test_require_cost_approval_blocks_when_unknown(monkeypatch):
    _reset_caches()
    monkeypatch.setattr(apify, "_actor_primary_event_price_usd", lambda actor_id, event_key=None: None)
    try:
        apify._require_cost_approval("some~actor", 1, approved=False)
    except apify.ApifyCostApprovalRequired as exc:
        assert exc.estimated_usd is None
    else:
        raise AssertionError("expected ApifyCostApprovalRequired for unknown cost")


def test_require_cost_approval_allows_under_threshold(monkeypatch):
    _reset_caches()
    monkeypatch.setattr(apify, "_actor_primary_event_price_usd", lambda actor_id, event_key=None: 0.002)
    apify._require_cost_approval("some~actor", 5, approved=False)  # $0.01, no raise


def test_require_cost_approval_at_threshold_is_allowed(monkeypatch):
    # Exactly the threshold should not require approval (gate is "> threshold").
    _reset_caches()
    monkeypatch.setattr(apify, "_actor_primary_event_price_usd", lambda actor_id, event_key=None: 0.01)
    apify._require_cost_approval("some~actor", 10, approved=False)  # exactly $0.10


# --- wrapper wiring: each function gates before running -----------------------

def test_verify_emails_blocks_over_threshold_before_running(monkeypatch):
    _reset_caches()
    monkeypatch.setattr(apify, "_actor_primary_event_price_usd", lambda actor_id, event_key=None: 1.0)

    def boom(*a, **k):
        raise AssertionError("run_actor should not be called when cost-gated")
    monkeypatch.setattr(apify, "run_actor", boom)
    try:
        apify.verify_emails(["a@b.com"])
    except apify.ApifyCostApprovalRequired:
        pass
    else:
        raise AssertionError("expected ApifyCostApprovalRequired")


def test_verify_emails_runs_when_approved(monkeypatch):
    _reset_caches()

    def boom(actor_id, event_key=None):
        raise AssertionError("should not estimate when already approved")
    monkeypatch.setattr(apify, "_actor_primary_event_price_usd", boom)
    monkeypatch.setattr(apify, "run_actor", lambda *a, **k: [{"email": "a@b.com", "status": "ok"}])
    out = apify.verify_emails(["a@b.com"], approved=True)
    assert out[0]["email"] == "a@b.com"


def test_instagram_gates_on_limit(monkeypatch):
    _reset_caches()
    monkeypatch.setattr(apify, "_actor_primary_event_price_usd", lambda actor_id, event_key=None: 0.01)

    def boom(*a, **k):
        raise AssertionError("run_actor should not be called when cost-gated")
    monkeypatch.setattr(apify, "run_actor", boom)
    try:
        apify.instagram("https://instagram.com/x", limit=50)  # $0.50
    except apify.ApifyCostApprovalRequired:
        pass
    else:
        raise AssertionError("expected ApifyCostApprovalRequired")


def test_instagram_routes_details_to_profile_actor_posts_to_post_actor(monkeypatch):
    # The Instagram split (2026-07-18): details -> instagram-profile-scraper
    # (usernames input), posts -> instagram-post-scraper (username input).
    _reset_caches()
    monkeypatch.setattr(apify, "_actor_primary_event_price_usd", lambda actor_id, event_key=None: 0.001)
    seen = {}

    def fake_run(actor_id, run_input, **k):
        seen["actor"] = actor_id
        seen["input"] = run_input
        return []
    monkeypatch.setattr(apify, "run_actor", fake_run)

    apify.instagram("https://www.instagram.com/coachjane/?hl=en", mode="details")
    assert seen["actor"] == apify.ACTORS["ig_profile"]
    assert seen["input"] == {"usernames": ["coachjane"]}

    apify.instagram("https://www.instagram.com/coachjane/", mode="posts",
                    limit=5, newer_than="60 days", skip_pinned=True)
    assert seen["actor"] == apify.ACTORS["ig_post"]
    assert seen["input"]["username"] == ["https://www.instagram.com/coachjane/"]
    assert seen["input"]["resultsLimit"] == 5
    assert seen["input"]["onlyPostsNewerThan"] == "60 days"
    assert seen["input"]["skipPinnedPosts"] is True


def test_instagram_post_routes_to_post_actor(monkeypatch):
    _reset_caches()
    monkeypatch.setattr(apify, "_actor_primary_event_price_usd", lambda actor_id, event_key=None: 0.001)
    seen = {}

    def fake_run(actor_id, run_input, **k):
        seen["actor"] = actor_id
        seen["input"] = run_input
        return []
    monkeypatch.setattr(apify, "run_actor", fake_run)
    apify.instagram_post("https://www.instagram.com/p/ABC123/")
    assert seen["actor"] == apify.ACTORS["ig_post"]
    assert seen["input"] == {"username": ["https://www.instagram.com/p/ABC123/"], "resultsLimit": 1}


def test_ig_username_normalizes_urls_and_handles(monkeypatch=None):
    assert apify._ig_username("coachjane") == "coachjane"
    assert apify._ig_username("@coachjane") == "coachjane"
    assert apify._ig_username("https://www.instagram.com/coachjane/?hl=en") == "coachjane"
    assert apify._ig_username("instagram.com/coachjane") == "coachjane"


def test_linkedin_profile_routes_to_harvestapi_with_mode_string(monkeypatch):
    # The li_profile swap back to harvestapi (2026-07-31): `queries` input,
    # and a profileScraperMode enum string the actor matches exactly.
    _reset_caches()
    monkeypatch.setattr(apify, "_actor_primary_event_price_usd",
                        lambda actor_id, event_key=None: 0.004)
    seen = {}

    def fake_run(actor_id, run_input, **k):
        seen["actor"] = actor_id
        seen["input"] = run_input
        return []
    monkeypatch.setattr(apify, "run_actor", fake_run)

    apify.linkedin_profile("https://www.linkedin.com/in/coachjane")
    assert seen["actor"] == "harvestapi~linkedin-profile-scraper"
    assert seen["input"] == {
        "queries": ["https://www.linkedin.com/in/coachjane"],
        "profileScraperMode": "Profile details no email ($4 per 1k)",
    }

    apify.linkedin_profile("coachjane", with_email=True)
    assert seen["input"]["profileScraperMode"] == "Profile details + email search ($10 per 1k)"


def test_linkedin_profile_gates_on_the_mode_actually_being_run(monkeypatch):
    # The email mode bills a different event; the estimate must price that
    # one, not assume the cheap mode.
    _reset_caches()
    asked = []
    monkeypatch.setattr(apify, "run_actor", lambda *a, **k: [])

    def fake_price(actor_id, event_key=None):
        asked.append(event_key)
        return 0.004
    monkeypatch.setattr(apify, "_actor_primary_event_price_usd", fake_price)
    apify.linkedin_profile("coachjane")
    apify.linkedin_profile("coachjane", with_email=True)
    assert asked == ["profile", "profile_with_email"]


def test_linkedin_profile_normalizes_harvestapi_output(monkeypatch):
    # harvestapi is flat where apimaestro nested under basic_info — callers
    # must keep seeing the same keys across the swap.
    _reset_caches()
    monkeypatch.setattr(apify, "_actor_primary_event_price_usd",
                        lambda actor_id, event_key=None: 0.004)
    monkeypatch.setattr(apify, "run_actor", lambda *a, **k: [{
        "linkedinUrl": "https://www.linkedin.com/in/coachjane",
        "publicIdentifier": "coachjane",
        "firstName": "Jane",
        "lastName": "Doe",
        "headline": "Leadership coach",
        "about": "I coach founders.",
        "location": {"linkedinText": "Dubai, United Arab Emirates"},
        "currentPosition": [{"companyName": "Jane Doe Coaching"}],
        "followerCount": 4097,
        "websites": ["https://janedoe.ae"],
        "emails": [
            {"email": "stale@old.com", "status": "invalid", "deliverable": False},
            {"email": "jane@janedoe.ae", "status": "valid", "deliverable": True},
        ],
        "experience": [
            {"position": "Founder", "companyName": "Jane Doe Coaching",
             "location": "Dubai", "duration": "4 yrs",
             "endDate": {"text": "Present"}},
            {"position": "Consultant", "companyName": "Someone Else",
             "endDate": {"text": "2021"}},
        ],
    }])
    rec = apify.linkedin_profile("coachjane", with_email=True)[0]
    assert rec["fullName"] == "Jane Doe"
    assert rec["location"] == "Dubai, United Arab Emirates"
    assert rec["currentCompany"] == "Jane Doe Coaching"
    assert rec["followerCount"] == 4097
    assert rec["website"] == "https://janedoe.ae"
    # the deliverable address wins over the first one listed
    assert rec["email"] == "jane@janedoe.ae"
    assert rec["experience"][0] == {
        "title": "Founder", "company": "Jane Doe Coaching",
        "location": "Dubai", "duration": "4 yrs", "is_current": True,
    }
    # a finished role carries no is_current key at all, rather than False
    assert "is_current" not in rec["experience"][1]


def test_linkedin_profile_falls_back_to_an_unverified_address(monkeypatch):
    # No address is verified-valid: return the one we have rather than none —
    # email-verify re-checks it downstream anyway.
    _reset_caches()
    monkeypatch.setattr(apify, "_actor_primary_event_price_usd",
                        lambda actor_id, event_key=None: 0.01)
    monkeypatch.setattr(apify, "run_actor", lambda *a, **k: [{
        "publicIdentifier": "coachjane",
        "emails": [{"email": "jane@janedoe.ae", "status": "unknown"}],
    }])
    assert apify.linkedin_profile("coachjane", with_email=True)[0]["email"] == "jane@janedoe.ae"


def test_linkedin_profile_surfaces_actor_side_failure(monkeypatch):
    # An unresolvable profile comes back as an `error` field in a 200 response;
    # it must not read as an empty-but-valid profile.
    _reset_caches()
    monkeypatch.setattr(apify, "_actor_primary_event_price_usd",
                        lambda actor_id, event_key=None: 0.004)
    monkeypatch.setattr(apify, "run_actor", lambda *a, **k: [
        {"error": "not_found", "errorDescription": "profile does not exist"}])
    try:
        apify.linkedin_profile("ghost")
    except apify.ApifyError as exc:
        assert "ghost" in str(exc)
    else:
        raise AssertionError("expected ApifyError on an actor-side failure")


def test_footprint_search_forwards_approved_to_both_google_search_calls(monkeypatch):
    _reset_caches()
    calls = []

    def fake_google_search(query, **kw):
        calls.append(kw.get("approved"))
        return []
    monkeypatch.setattr(apify, "google_search", fake_google_search)
    apify.footprint_search("kajabi", approved=True)
    assert calls and all(calls)


if __name__ == "__main__":
    import unittest.mock as _mock

    class _MonkeyPatch:
        def __init__(self):
            self._undo = []

        def setattr(self, obj, name, value):
            self._undo.append((obj, name, getattr(obj, name)))
            setattr(obj, name, value)

        def undo(self):
            for obj, name, old in reversed(self._undo):
                setattr(obj, name, old)

    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        mp = _MonkeyPatch()
        try:
            fn(mp)
            print(f"ok   {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
        finally:
            mp.undo()
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
