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
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Standalone runs get no conftest, and every wrapper here writes a ledger line.
os.environ.setdefault("OUTBOUND_LEDGER_ROOT",
                      tempfile.mkdtemp(prefix="outbound-ledger-"))

# No token, so nothing here can reach Apify even by accident. This file stubs
# `requests.get` and `run_actor` per test, and that was believed to be enough
# until the approval gate started pricing the approved path too: on a machine
# with APIFY_TOKEN set, ten tests that stub only `run_actor` began making real
# pricing calls and passing, and the same ten failed in CI where there is no
# token. The suite must not depend on who ran it — the same reason
# `test_cli_failures.offline_env()` pops AIRTABLE_API_KEY.
for _var in ("APIFY_TOKEN", "APIFY_API_TOKEN"):
    os.environ.pop(_var, None)

from audit import apify
from outbound import ledger


class _FakeResponse:
    def __init__(self, payload, ok=True, status_code=200, text=""):
        self._payload = payload
        self.ok = ok
        self.status_code = status_code
        # Only the not-ok branch of run_actor reads this, to quote the body back.
        self.text = text

    def json(self):
        return self._payload


def _reset_caches():
    apify._pricing_cache.clear()
    apify._compute_billed.clear()
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
    # A verification actor's real pricing shape: no event is flagged
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
    assert apify._actor_primary_event_price_usd("michael.g~email-verifier-validator") == 0.001


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


def test_require_cost_approval_passes_but_still_prices_when_approved(monkeypatch):
    """approved=True must never block. It DOES still price the run.

    This used to short-circuit before estimating at all, and the consequence
    only became visible when the ledger arrived: the runs signed off as
    expensive were the runs nothing recorded a price for. The estimate is
    cached per actor per process, so the cost is one lookup, and it buys a
    figure for exactly the calls worth having one.
    """
    _reset_caches()
    monkeypatch.setattr(apify, "_actor_primary_event_price_usd",
                        lambda actor_id, event_key=None: 0.002)
    assert apify._require_cost_approval("some~actor", 999, approved=True) == 1.998


def test_an_unpriceable_run_is_still_approvable(monkeypatch):
    """Pricing that cannot be read must not turn into a block on a call
    Haytham already signed off. None is the honest cost, not a refusal."""
    _reset_caches()
    monkeypatch.setattr(apify, "_actor_primary_event_price_usd",
                        lambda actor_id, event_key=None: None)
    assert apify._require_cost_approval("some~actor", 5, approved=True) is None


def test_an_approved_run_does_not_fail_when_pricing_cannot_be_looked_up():
    """The regression this pins for real: pricing needs a token, so making the
    gate always estimate turned "no APIFY_TOKEN" into an exception raised by the
    approval gate — a call already signed off failing on the accounting rather
    than on the work. CI caught it; a developer machine with a token could not.
    On the approved path the number is for the ledger, so it is best-effort."""
    _reset_caches()
    assert apify._require_cost_approval("some~actor", 5, approved=True) is None


def test_an_unapproved_run_with_no_token_fails_on_the_token():
    """The other half, and the asymmetry is deliberate.

    Unapproved, a missing token surfaces as the token error rather than a cost
    refusal — pricing reads `_auth_headers` before it reads anything else, and
    "APIFY_TOKEN is not set" is the more useful sentence than "cannot estimate"
    for a run that could not have happened either way. What matters is that it
    raises at all: failing to price must never become permission to spend.
    """
    _reset_caches()
    try:
        apify._require_cost_approval("some~actor", 5, approved=False)
    except apify.ApifyError:
        return
    raise AssertionError("no price must never pass through to a run")


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

    monkeypatch.setattr(apify, "_actor_primary_event_price_usd",
                        lambda actor_id, event_key=None: 0.001)
    monkeypatch.setattr(apify, "run_actor", lambda *a, **k: [{"email": "a@b.com", "status": "ok"}])
    out = apify.verify_emails(["a@b.com"], approved=True)
    assert out[0]["email"] == "a@b.com"


def test_verify_emails_calls_the_one_vetted_verifier(monkeypatch):
    # The predecessor spent a guaranteed-useless call per address for a day
    # while it was down, then sat behind a flag. There is one actor now, and
    # nothing should be able to reintroduce a second call site quietly.
    _reset_caches()
    called = []

    def record(actor_id, run_input, **kwargs):
        called.append(actor_id)
        return [{"email": "a@b.com", "technical_status": "valid"}]
    monkeypatch.setattr(apify, "run_actor", record)
    apify.verify_emails(["a@b.com"], approved=True)
    assert called == ["michael.g~email-verifier-validator"]
    assert "email_alt" not in apify.ACTORS


def test_verify_emails_returns_a_row_for_every_address_asked_about(monkeypatch):
    # It used to drop them. A caller then got back fewer rows than it asked
    # for with no way to tell which address had gone missing — the same
    # silence as the outage this actor set was rebuilt around.
    _reset_caches()
    monkeypatch.setattr(
        apify, "run_actor",
        lambda *a, **k: [{"email": "b@y.ae", "technical_status": "valid"}])
    out = apify.verify_emails(["a@x.ae", "b@y.ae", "c@z.ae"], approved=True)
    assert [r["email"] for r in out] == ["a@x.ae", "b@y.ae", "c@z.ae"]
    assert [r["result"] for r in out] == ["no_result", "valid", "no_result"]


def test_verify_emails_keeps_an_actor_error_distinct_from_unknown(monkeypatch):
    # Both classify to WARN, so the verdict is unchanged — but `error` means
    # the actor could not look and `unknown` means it looked and could not
    # tell. Collapsing them is what hid a dead verifier for 40 leads.
    _reset_caches()
    monkeypatch.setattr(
        apify, "run_actor",
        lambda *a, **k: [{"email": "a@x.ae", "technical_status": "error"},
                         {"email": "b@y.ae", "technical_status": "unknown"}])
    out = apify.verify_emails(["a@x.ae", "b@y.ae"], approved=True)
    assert [r["result"] for r in out] == ["error", "unknown"]


def test_verify_emails_reads_catch_all_and_disposable_ahead_of_the_status(monkeypatch):
    _reset_caches()
    monkeypatch.setattr(
        apify, "run_actor",
        lambda *a, **k: [{"email": "a@x.ae", "technical_status": "valid", "catch_all": True},
                         {"email": "b@y.ae", "technical_status": "valid", "disposable": True}])
    out = apify.verify_emails(["a@x.ae", "b@y.ae"], approved=True)
    assert [r["result"] for r in out] == ["catch_all", "disposable"]


def test_verify_emails_says_who_answered(monkeypatch):
    _reset_caches()
    monkeypatch.setattr(
        apify, "run_actor",
        lambda *a, **k: [{"email": "a@x.ae", "technical_status": "valid"}])
    assert apify.verify_emails(["a@x.ae"], approved=True)[0]["verified_by"] == "apify"


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


# --- the two site actors, and the two ways a run can be unpriceable ----------


def test_a_compute_billed_actor_says_so_instead_of_looking_broken(monkeypatch):
    """Apify's own free actors carry no pricingInfos at all. That is a known
    pricing model, not a failed lookup, and collapsing the two into one message
    is the same class of bug as an actor outage reading like a catch-all."""
    _reset_caches()
    monkeypatch.setattr(apify, "_auth_headers", lambda: {})
    monkeypatch.setattr(apify.requests, "get",
                        lambda *a, **k: _FakeResponse({"data": {}}))
    est, reason = apify.estimate_cost_usd("apify~cheerio-scraper", 40)
    assert est is None
    assert "platform compute" in reason
    assert "retrying will not change it" in reason


def test_a_real_lookup_failure_still_reads_as_one(monkeypatch):
    _reset_caches()
    monkeypatch.setattr(apify, "_auth_headers", lambda: {})

    def down(*a, **k):
        raise apify.requests.RequestException("down")
    monkeypatch.setattr(apify.requests, "get", down)
    est, reason = apify.estimate_cost_usd("some~actor", 5)
    assert est is None and "network error" in reason


def test_both_site_actors_are_vetted():
    """The escalation plan used to name an actor id that was in no ACTORS map,
    so nothing could run it through the cost gate and the first real batch
    skipped the whole stage."""
    assert apify.ACTORS["site_static"] == "apify~cheerio-scraper"
    assert apify.ACTORS["site_render"] == "apify~website-content-crawler"


def test_crawl_static_batches_every_url_into_one_run(monkeypatch):
    """Container boot dominates the bill. Fifty separate runs is the worst
    possible way to use a compute-billed actor."""
    _reset_caches()
    seen = {}

    def record(actor_id, run_input, **kwargs):
        seen["actor"], seen["input"] = actor_id, run_input
        return [{"url": "https://a.ae", "text": "hi"}]
    monkeypatch.setattr(apify, "run_actor", record)
    apify.crawl_static(["https://a.ae", "https://b.ae", "https://a.ae"],
                       approved=True)
    assert seen["actor"] == "apify~cheerio-scraper"
    assert [s["url"] for s in seen["input"]["startUrls"]] == [
        "https://a.ae", "https://b.ae"]          # deduped, one run
    assert "pageFunction" in seen["input"]


def test_crawl_render_always_names_its_crawler_type(monkeypatch):
    """Leaving `crawlerType` unset is what silently bought full headless
    Firefox on a run that cost six times its estimate. Untested until now."""
    _reset_caches()
    seen = {}
    monkeypatch.setattr(apify, "run_actor",
                        lambda actor_id, run_input, **k: seen.update(
                            actor=actor_id, input=run_input) or [])
    apify.crawl_render(["https://a.ae"], approved=True)
    assert seen["actor"] == "apify~website-content-crawler"
    assert seen["input"]["crawlerType"] == "playwright:adaptive"


def test_the_site_crawlers_gate_before_running(monkeypatch):
    _reset_caches()
    monkeypatch.setattr(apify, "_actor_primary_event_price_usd",
                        lambda actor_id, event_key=None: 1.0)

    def boom(*a, **k):
        raise AssertionError("run_actor should not be called when cost-gated")
    monkeypatch.setattr(apify, "run_actor", boom)
    for call in (apify.crawl_static, apify.crawl_render):
        try:
            call(["https://a.ae"])
        except apify.ApifyCostApprovalRequired:
            continue
        raise AssertionError(f"{call.__name__} should have been gated")


def test_instagram_details_batches_several_profiles_into_one_run(monkeypatch):
    """The profile actor's input field is `usernames`, an array — so batching
    is free, the same lever li-profile and verify-email already pull."""
    _reset_caches()
    seen = {}

    def record(actor_id, run_input, **kwargs):
        seen["actor"], seen["input"] = actor_id, run_input
        return [{"username": "b", "biography": "second"},
                {"username": "a", "biography": "first"}]
    monkeypatch.setattr(apify, "run_actor", record)
    out = apify.instagram(["https://instagram.com/a/", "https://instagram.com/b"],
                          mode="details", approved=True)
    assert seen["actor"] == apify.ACTORS["ig_profile"]
    assert seen["input"]["usernames"] == ["a", "b"]
    # Correlated back to input order, not the order the actor answered in.
    assert [r["username"] for r in out] == ["a", "b"]


def test_a_profile_the_actor_could_not_read_is_a_none_not_a_short_list(monkeypatch):
    _reset_caches()
    monkeypatch.setattr(apify, "run_actor",
                        lambda *a, **k: [{"username": "a", "biography": "hi"}])
    out = apify.instagram(["https://instagram.com/a", "https://instagram.com/gone"],
                          mode="details", approved=True)
    assert len(out) == 2 and out[1] is None


def test_instagram_posts_refuses_a_list(monkeypatch):
    """li-posts was batched, tested, and turned out to share `maxPosts` across
    every target as one run-wide budget — two profiles, a cap of ten, all ten
    posts from one and nothing from the other. Nobody has tested whether this
    actor's resultsLimit behaves the same, and assuming it does not is how a
    batch silently loses its post data and reads as "no recent activity"."""
    _reset_caches()
    monkeypatch.setattr(apify, "run_actor", lambda *a, **k: [])
    try:
        apify.instagram(["https://instagram.com/a", "https://instagram.com/b"],
                        mode="posts", approved=True)
    except apify.ApifyError as exc:
        assert "run-wide budget" in str(exc)
        return
    raise AssertionError("mode='posts' must refuse more than one profile")


def test_a_single_instagram_profile_still_returns_a_flat_list(monkeypatch):
    _reset_caches()
    monkeypatch.setattr(apify, "run_actor",
                        lambda *a, **k: [{"username": "a", "biography": "hi"}])
    out = apify.instagram("https://instagram.com/a", mode="details", approved=True)
    assert out[0]["username"] == "a"


def test_instagram_details_gates_on_the_number_of_profiles(monkeypatch):
    _reset_caches()
    seen = {}
    monkeypatch.setattr(apify, "_actor_primary_event_price_usd",
                        lambda actor_id, event_key=None: 0.02)
    monkeypatch.setattr(apify, "run_actor", lambda *a, **k: seen.update(ran=True) or [])
    try:
        apify.instagram([f"https://instagram.com/u{i}" for i in range(6)],
                        mode="details")
    except apify.ApifyCostApprovalRequired:
        assert not seen.get("ran"), "gated calls must not run"
        return
    raise AssertionError("6 profiles at $0.02 is $0.12, over the threshold")


# ------------------------------------------------------------------ the ledger
#
# The cost gate is where the only dollar figure in this repo is produced, so it
# is also where the ledger gets its numbers. Before this, `_require_cost_approval`
# computed the estimate, compared it, and dropped it — the figure survived only
# inside the exception raised when the gate refused, which meant every run that
# was allowed to happen went unpriced. These pin that the number now reaches the
# record, on both the allowed path and the refused one.


def test_an_allowed_run_records_what_it_was_priced_at(monkeypatch, tmp_path):
    _reset_caches()
    monkeypatch.setenv("OUTBOUND_LEDGER_ROOT", str(tmp_path))
    monkeypatch.setattr(apify, "_actor_primary_event_price_usd",
                        lambda actor_id, event_key=None: 0.004)
    monkeypatch.setattr(apify.requests, "post",
                        lambda *a, **k: _FakeResponse([{"content": "a post"}]))
    monkeypatch.setattr(apify, "_auth_headers", lambda: {})

    apify.linkedin_posts("https://linkedin.com/in/x", max_posts=5)

    records, _ = ledger.read(None, tmp_path)
    assert len(records) == 1
    assert records[0].retrieved_by == "apify:li_posts"
    assert records[0].cost_usd == 0.02
    assert records[0].url == "https://linkedin.com/in/x"
    assert records[0].outcome == "ok"


def test_a_run_that_returned_nothing_is_recorded_as_empty(monkeypatch, tmp_path):
    """A paid run that came back empty still paid for its container boot. It is
    the single most interesting line in a batch that produced no hooks."""
    _reset_caches()
    monkeypatch.setenv("OUTBOUND_LEDGER_ROOT", str(tmp_path))
    monkeypatch.setattr(apify, "_actor_primary_event_price_usd",
                        lambda actor_id, event_key=None: 0.001)
    monkeypatch.setattr(apify.requests, "post", lambda *a, **k: _FakeResponse([]))
    monkeypatch.setattr(apify, "_auth_headers", lambda: {})

    apify.linkedin_posts("https://linkedin.com/in/x")

    records, _ = ledger.read(None, tmp_path)
    assert records[0].outcome == "empty"


def test_a_run_that_errored_is_still_recorded(monkeypatch, tmp_path):
    """A stage that spent ninety seconds failing is exactly what the ledger
    exists to surface. Recording only successes would hide it."""
    _reset_caches()
    monkeypatch.setenv("OUTBOUND_LEDGER_ROOT", str(tmp_path))
    monkeypatch.setattr(apify, "_actor_primary_event_price_usd",
                        lambda actor_id, event_key=None: 0.001)
    monkeypatch.setattr(apify.requests, "post",
                        lambda *a, **k: _FakeResponse({"error": "x"}, ok=False,
                                                      status_code=500))
    monkeypatch.setattr(apify, "_auth_headers", lambda: {})

    try:
        apify.linkedin_posts("https://linkedin.com/in/x")
    except apify.ApifyError:
        pass
    records, _ = ledger.read(None, tmp_path)
    assert records[0].outcome == "error"


def test_the_ledger_names_the_actor_key_not_the_rest_api_id(monkeypatch, tmp_path):
    """`apify:li_posts`, not `apify:harvestapi~linkedin-profile-posts`. The key
    is what the cost tables, the docs and the escalate plans already speak in."""
    _reset_caches()
    monkeypatch.setenv("OUTBOUND_LEDGER_ROOT", str(tmp_path))
    monkeypatch.setattr(apify, "_actor_primary_event_price_usd",
                        lambda actor_id, event_key=None: 0.0005)
    monkeypatch.setattr(apify.requests, "post",
                        lambda *a, **k: _FakeResponse([{"name": "a channel"}]))
    monkeypatch.setattr(apify, "_auth_headers", lambda: {})

    apify.youtube_channel("@somebody")

    records, _ = ledger.read(None, tmp_path)
    assert records[0].retrieved_by == "apify:yt_channel"
    assert records[0].platform == "youtube"


def test_every_actor_key_survives_the_round_trip():
    """The reverse map is built from ACTORS, so an actor added without a key —
    or a duplicate id across two keys — would silently mislabel its spend."""
    assert len(apify._ACTOR_KEYS) == len(apify.ACTORS)
    for key, actor_id in apify.ACTORS.items():
        assert apify._ACTOR_KEYS[actor_id] == key


# The no-pytest runner stays at the BOTTOM of this file, and that is not a
# style preference. It used to sit two-thirds of the way up, so the sixteen
# tests defined below it were never in `globals()` when it built its list —
# `python tests/test_apify_cost_gate.py` reported 39/39 while pytest ran 55.
# A standalone runner that silently skips a third of the file is worse than
# none, because the third it skips reports as a pass.
if __name__ == "__main__":
    import inspect

    class _MonkeyPatch:
        """Enough of pytest's fixture to run this file without pytest.

        It grew `setenv` and the signature dispatch below when the ledger tests
        arrived: the runner used to hand every test one positional argument, so
        a test taking `tmp_path`, or none at all, was a TypeError that only the
        no-pytest path could produce. A standalone runner that cannot run half
        the file is worse than no standalone runner, because it reports the
        other half as a pass.
        """

        def __init__(self):
            self._undo = []
            self._env = []

        def setattr(self, obj, name, value):
            self._undo.append((obj, name, getattr(obj, name)))
            setattr(obj, name, value)

        def setenv(self, name, value):
            self._env.append((name, os.environ.get(name)))
            os.environ[name] = str(value)

        def undo(self):
            for obj, name, old in reversed(self._undo):
                setattr(obj, name, old)
            for name, old in reversed(self._env):
                if old is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = old

    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        mp = _MonkeyPatch()
        scratch = tempfile.TemporaryDirectory(prefix="apify-test-")
        available = {"monkeypatch": mp, "tmp_path": Path(scratch.name)}
        try:
            fn(*[available[name] for name in
                 inspect.signature(fn).parameters])
            print(f"ok   {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
        finally:
            mp.undo()
            scratch.cleanup()
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
