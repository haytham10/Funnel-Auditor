"""Gate 0's price floor — the re-niche to UAE coaches with a live program at
AED 5,000+ (2026-07-28).

The floor exists because the market study's purchasing-power indicator is a
measured FAIL: a coach with an AED 800 program cannot make AED 900/call work at
ANY price we could charge, so a reply from her was never revenue. The old
response was to lower the price until a broke market could afford it, which is
solving a targeting problem with a discount.

Two properties are load-bearing and both are tested here:

1. **The band is not an exchange rate.** Floating currencies get a wide,
   deliberately crude band, and the gate only decides when EVERY rate in it
   agrees. Anything straddling the floor is NEEDS_REVIEW, never a coin flip.
2. **The scrape can promote but never kill.** A price scraped off her pages can
   confirm a rich lead automatically; it can never disqualify a poor-looking
   one, because application-only 1:1 work is routinely off-page.
"""

from audit.gates import (
    PROGRAM_PRICE_FLOOR_AED, evaluate_floors, parse_price_token, price_floor_input,
    to_aed_band, PASS, FAIL, NEEDS_REVIEW,
)


def _floors(**kw):
    return evaluate_floors(
        bio_link_alive=True, bio_link_error="", offer_evidence=["sales page: x"],
        email_capture_anywhere=True, followers=5000, **kw,
    )


def _price_verdict(**kw):
    return next(v for v in _floors(**kw).verdicts if v.name == "price_floor")


# --- the floor itself -------------------------------------------------------

def test_program_above_floor_passes():
    v = _price_verdict(top_program_price=8000, top_program_currency="AED")
    assert v.verdict == PASS
    assert "8,000" in v.evidence


def test_program_below_floor_fails_hard():
    v = _price_verdict(top_program_price=800, top_program_currency="AED")
    assert v.verdict == FAIL
    # The kill has to name its own escape hatch: a higher program the walk missed.
    assert "HIGHER live program" in v.evidence
    assert _floors(top_program_price=800).hard_fail


def test_price_exactly_at_the_floor_passes():
    # The floor is "AED 5,000 or above", not "above AED 5,000".
    assert _price_verdict(top_program_price=PROGRAM_PRICE_FLOOR_AED).verdict == PASS


def test_no_price_is_review_never_a_silent_pass():
    v = _price_verdict()
    assert v.verdict == NEEDS_REVIEW
    assert not _floors().hard_fail


# --- currency handling ------------------------------------------------------

def test_usd_uses_the_hard_peg_as_a_point_rate():
    # AED is pegged to USD by the central bank. That is not an estimate.
    low, high = to_aed_band(1000, "USD")
    assert low == high
    assert _price_verdict(top_program_price=2000, top_program_currency="USD").verdict == PASS


def test_gbp_clears_when_every_rate_in_the_band_agrees():
    # GBP 8,999 (Sadia Khan's real tier) is over the floor at any plausible rate.
    assert _price_verdict(top_program_price=8999, top_program_currency="GBP").verdict == PASS


def test_gbp_fails_when_every_rate_in_the_band_agrees():
    assert _price_verdict(top_program_price=200, top_program_currency="GBP").verdict == FAIL


def test_a_price_straddling_the_floor_is_never_decided_by_the_band():
    # GBP 1,200 is AED 4,560 at 3.8 and AED 6,480 at 5.4 — the band disagrees
    # with itself, so the gate must refuse to rule rather than pick a rate.
    v = _price_verdict(top_program_price=1200, top_program_currency="GBP")
    assert v.verdict == NEEDS_REVIEW
    assert "not an exchange rate" in v.evidence


def test_unknown_currency_is_review_not_a_guess():
    v = _price_verdict(top_program_price=50000, top_program_currency="JPY")
    assert v.verdict == NEEDS_REVIEW


# --- price token parsing ----------------------------------------------------

def test_parse_price_token_shapes():
    assert parse_price_token("AED 6,600") == (6600.0, "AED")
    assert parse_price_token("$8,999") == (8999.0, "USD")
    assert parse_price_token("1500 AED") == (1500.0, "AED")
    assert parse_price_token("£149.99") == (149.99, "GBP")


def test_an_unlabelled_number_is_not_a_price():
    # "2026" and "1,500" appear all over a coaching site. Without a currency
    # they are not prices and must never reach the floor.
    assert parse_price_token("2026") is None
    assert parse_price_token("1,500") is None


# --- the scrape can promote but never kill ----------------------------------

def test_scraped_price_above_floor_promotes_to_a_real_verdict():
    out = price_floor_input([("https://x.ae/work", ["AED 299", "AED 6,600"])])
    assert out["top_program_price"] == 6600.0
    assert out["top_program_currency"] == "AED"
    assert _price_verdict(**out).verdict == PASS


def test_scraped_price_below_floor_never_asserts_a_price():
    # THE regression. If this ever returns top_program_price, a scraped AED 299
    # workshop starts hard-failing coaches who sell AED 20,000 1:1 by
    # application, and a hard fail is permanent.
    out = price_floor_input([("https://x.ae/shop", ["AED 108", "AED 299"])])
    assert "top_program_price" not in out
    assert "NOT proof" in out["price_evidence"]
    assert _price_verdict(**out).verdict == NEEDS_REVIEW


def test_caller_filters_external_pages_so_none_reach_the_helper():
    # External/errored pages are dropped by the caller in evidence.py: a
    # competitor's AED 90,000 program on a page we merely crawled is not her
    # price. The helper only ever sees the lead's own pages.
    assert price_floor_input([]) == {}


def test_no_parseable_prices_yields_no_input_at_all():
    assert price_floor_input([("https://x.ae", ["2026", "50%"])]) == {}
