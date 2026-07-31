"""The three floors, and the research object's schema.

Run: python -m pytest tests/test_qualify.py -q
 or: python tests/test_qualify.py

The asymmetry these tests exist to protect: `unclear` passes, and only a clear
`no` drops a row. A false kill is permanent and invisible; a false pass costs
one more research call. Any change that makes `unclear` start killing leads is
a regression even if every individual verdict looks more "correct".
"""

import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from outbound import qualify as q
from outbound import research as r

TODAY = date(2026, 7, 31)


# ------------------------------------------------------------------ UAE floor


def test_a_named_emirate_passes():
    assert q.check_uae(city="Dubai").value == q.YES


def test_a_dot_ae_domain_passes():
    assert q.check_uae(domain="sarahcoaching.ae").value == q.YES


def test_a_dubai_district_passes():
    assert q.check_uae(text="Our studio sits in JLT.").value == q.YES


def test_serving_the_uae_from_elsewhere_does_not_pass():
    """A coach in London selling into Dubai has a different market, a different
    price ceiling, and no reason to recognise the reference group."""
    verdict = q.check_uae(text="Serving the UAE and the wider GCC since 2019.")
    assert verdict.value == q.UNCLEAR
    assert "residence" in verdict.evidence


def test_a_clearly_stated_other_country_fails():
    assert q.check_uae(text="Based in Manchester, working worldwide.").value == q.NO


def test_no_data_is_unclear_not_no():
    assert q.check_uae().value == q.UNCLEAR


def test_a_uae_verdict_carries_its_evidence():
    verdict = q.check_uae(city="Abu Dhabi")
    assert verdict.evidence == "abu dhabi"


def test_uae_shorthand_in_a_based_in_line_passes():
    """"Based in DXB" returned a hard NO, because the parser recognised the
    "based in" shape and then failed to recognise the place. That is the exact
    false kill the design forbids, on a lead who told us she is here."""
    for text in ("Based in DXB.", "Based in AUH, working across the Emirates.",
                 "based in RAK"):
        assert q.check_uae(text=text).value == q.YES, text


def test_a_uae_neighbourhood_passes():
    """Eleven real UAE localities returned a hard NO, because the rule killed
    on any place it did not recognise. "Based in Al Barsha" is a Dubai coach
    telling us exactly where she is."""
    for place in ("Al Barsha", "Deira", "Mirdif", "Motor City", "Al Quoz",
                  "Emirates Hills", "The Greens", "Arabian Ranches",
                  "Reem Island", "Al Nahda", "Bur Dubai"):
        assert q.check_uae(text=f"Based in {place}.").value == q.YES, place


def test_an_unrecognised_place_is_unclear_not_no():
    """The burden sits on the kill. Not recognising a place is a fact about our
    list, not about the lead — and a false kill is permanent and invisible."""
    for place in ("BLR", "Zzyzx", "Blugton"):
        assert q.check_uae(text=f"Based in {place}.").value == q.UNCLEAR, place


def test_a_recognised_foreign_place_still_fails():
    for place in ("Manchester", "London", "New York", "Mumbai", "Riyadh",
                  "Doha", "Singapore", "the United Kingdom", "India"):
        assert q.check_uae(text=f"Based in {place}.").value == q.NO, place


# ---------------------------------------------------------------- coach floor


def test_a_coaching_headline_passes():
    assert q.check_coach(headline="Leadership Coach").value == q.YES


def test_silence_is_unclear_not_no():
    """Absence of the word 'coach' is absence of evidence, and this floor
    never returns a hard no on it."""
    assert q.check_coach(text="I help people grow.").value == q.UNCLEAR


# ------------------------------------------------------------- activity floor


def test_a_recent_post_passes():
    assert q.check_active(last_seen=TODAY - timedelta(days=5), today=TODAY).value == q.YES


def test_the_window_boundary_passes():
    assert q.check_active(last_seen=TODAY - timedelta(days=30), today=TODAY).value == q.YES


def test_a_stale_post_fails():
    assert q.check_active(last_seen=TODAY - timedelta(days=90), today=TODAY).value == q.NO


def test_no_dated_activity_is_unclear_not_no():
    """Plenty of working coaches do not post. Absence of a visible post is not
    evidence of an absent business."""
    assert q.check_active(last_seen=None, today=TODAY).value == q.UNCLEAR


def test_a_future_date_is_unclear():
    assert q.check_active(last_seen=TODAY + timedelta(days=5), today=TODAY).value == q.UNCLEAR


# ------------------------------------- the mechanical bridge from page to date


def _active(text, url=""):
    seen, why = q.latest_activity_date(text, page_url=url, today=TODAY)
    return q.check_active(last_seen=seen, today=TODAY, source=why).value


def test_a_recent_dated_post_settles_the_floor_without_an_agent():
    fresh = (TODAY - timedelta(days=6)).isoformat()
    assert _active(f"Latest article {fresh}. Three ways to price a package.") == q.YES


def test_an_old_dated_post_fails_the_floor():
    stale = (TODAY - timedelta(days=200)).isoformat()
    assert _active(f"Latest article {stale}.") == q.NO


def test_a_footer_copyright_year_is_not_activity():
    """"© 2026" is the footer's opinion of the current year, not evidence that
    anyone did anything."""
    assert _active(f"© {TODAY.year} Coach Co. All rights reserved.") == q.UNCLEAR


def test_a_footer_copyright_does_not_suppress_a_real_date_on_the_same_page():
    """The copyright test reads a tight window, not the ±80-char context. On
    the wide window every date on any page with a footer was discarded, which
    is every page."""
    fresh = (TODAY - timedelta(days=6)).isoformat()
    page = f"Latest article {fresh}. " + "filler " * 20 + f"© {TODAY.year} Coach Co."
    assert _active(page) == q.YES


def test_a_date_with_no_year_written_on_it_is_unclear():
    """`extract_dates` assumes the current year for those, which would read a
    "March 14" from three years ago as this March and pass a dead site."""
    assert _active("Join us March 14 for the workshop.") == q.UNCLEAR


def test_an_undated_page_is_unclear_not_no():
    assert _active("I help leaders find their edge. Book a call.") == q.UNCLEAR


def test_a_malformed_page_is_unclear_not_a_crash():
    assert _active("\x00�" * 50) == q.UNCLEAR


# ------------------------------------------------------------------- capture


def test_linkedin_wins_a_coach_type_conflict():
    """A real case: her site read Life/Mindset while her LinkedIn headline said
    Leadership & Performance Coach for corporate teams. Two offers, one name.
    LinkedIn is the paid-facing profile and is the more explicit of the two."""
    label, source = q.classify_coach_type(
        linkedin_text="Leadership & Performance Coach for senior teams",
        site_text="The Life Design Method, find your purpose")
    assert label == "Leadership"
    assert "site said Life" in source


def test_the_site_is_used_when_linkedin_is_silent():
    label, source = q.classify_coach_type(site_text="Health coach and nutrition guide")
    assert (label, source) == ("Health", "site")


def test_sells_to_is_read_not_guessed():
    label, _ = q.classify_sells_to(linkedin_text="I run in-house workshops for L&D teams")
    assert label == "corporates"
    label, _ = q.classify_sells_to(site_text="1:1 coaching for private clients")
    assert label == "individuals"


def test_a_page_claiming_both_audiences_says_nothing():
    """The old pipeline inferred this from hook keywords and its own doc
    expected the guess to be wrong on edge cases. An empty answer draws a
    generic identity line, which is honest."""
    label, _ = q.classify_sells_to(
        site_text="1:1 coaching for private clients and workshops for corporate teams")
    assert label == ""


def test_no_signal_returns_empty_rather_than_a_guess():
    assert q.classify_sells_to() == ("", "")


# ---------------------------------------------------------------- the verdict


def test_all_three_floors_unclear_still_passes():
    result = q.qualify(today=TODAY)
    assert result.passed
    assert result.failed_floors == []


def test_one_clear_no_fails_the_lead():
    result = q.qualify(site_text="Based in Manchester, working worldwide.",
                       today=TODAY)
    assert not result.passed
    assert "UAE-based" in result.failed_floors


def test_captured_fields_never_gate():
    """Audience and price are captured for the identity match and for cohort
    analysis. Neither one can kill a lead."""
    result = q.qualify(city="Dubai", headline="Life coach",
                       last_activity=TODAY, today=TODAY,
                       audience_size=12, top_program_price_aed=900)
    assert result.passed
    assert result.audience_size == 12
    assert result.top_program_price_aed == 900


def test_the_report_shows_every_source():
    result = q.qualify(city="Dubai", headline="Career coach",
                       last_activity=TODAY, today=TODAY)
    text = result.report("Sarah")
    assert "PASS" in text and "UAE-based: YES" in text and "captured:" in text


# ------------------------------------------------------- the research schema


def valid_research(**overrides):
    data = dict(
        slug="sarah-khan", name="Sarah Khan",
        uae_based="yes", uae_based_source="site: Dubai",
        active_recent="yes", active_recent_source="linkedin post 2026-07-20",
        is_coach="yes", is_coach_source="headline",
        coach_type="Health", coach_type_source="linkedin",
        sells_to="individuals", sells_to_source="site",
        email="sarah@site.ae", email_status="pass", email_source="contact page",
        hook="You wrote about your diagnosis.", hook_type="LIFE",
        hook_source_url="https://linkedin.com/posts/x",
        hook_quote="couldn't contain the excitement",
        hook_verified="verified",
        last_activity="2026-07-20",
    )
    data.update(overrides)
    return r.Research.from_dict(data)


def test_a_complete_object_validates():
    assert r.validate(valid_research()) == []


def test_a_verdict_outside_the_enum_is_caught():
    problems = r.validate(valid_research(uae_based="probably"))
    assert any("not one of" in p for p in problems)


def test_a_hard_verdict_with_no_source_is_caught():
    """A verdict that names nothing was reasoned, not fetched. This is the one
    check the independent verifier exists to enforce."""
    problems = r.validate(valid_research(uae_based_source=""))
    assert any("reasoned, not fetched" in p for p in problems)


def test_unclear_needs_no_source():
    assert r.validate(valid_research(solo="unclear", solo_source="")) == []


def test_an_audience_number_with_no_source_is_caught():
    """A soft pass on an audience number is what burned full walks under the
    old machine. Never guess a count."""
    problems = r.validate(valid_research(audience_size=4200, audience_source=""))
    assert any("never guess a count" in p for p in problems)


def test_a_hook_without_a_citation_is_caught():
    problems = r.validate(valid_research(hook_source_url=""))
    assert any("a citation or it is nothing" in p for p in problems)


def test_a_citation_with_no_quote_is_caught():
    problems = r.validate(valid_research(hook_quote=""))
    assert any("quotes nothing" in p for p in problems)


def test_a_malformed_address_is_caught():
    assert any("malformed" in p for p in r.validate(valid_research(email="sarah at site")))


def test_a_bad_date_is_caught():
    assert any("ISO date" in p for p in r.validate(valid_research(last_activity="July 20")))


def test_ready_to_draft_requires_everything():
    assert valid_research().ready_to_draft
    assert not valid_research(hook_verified="proposed").ready_to_draft
    assert not valid_research(email_status="warn").ready_to_draft
    assert not valid_research(uae_based="no").ready_to_draft


def test_blockers_name_what_is_missing():
    blockers = valid_research(email="", hook_verified="refuted").blockers()
    assert any("no email address" in b for b in blockers)
    assert any("refuted" in b for b in blockers)


def test_unclear_floors_do_not_block_drafting():
    assert valid_research(uae_based="unclear", uae_based_source="").ready_to_draft


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  ok    {name}")
            except AssertionError as exc:
                failures += 1
                print(f"  FAIL  {name}: {exc}")
    print(f"\n{failures} failure(s)")
    sys.exit(1 if failures else 0)
