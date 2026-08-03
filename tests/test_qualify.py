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
    false kill the design forbids, on a lead who told us they are here."""
    for text in ("Based in DXB.", "Based in AUH, working across the Emirates.",
                 "based in RAK"):
        assert q.check_uae(text=text).value == q.YES, text


def test_a_uae_neighbourhood_passes():
    """Eleven real UAE localities returned a hard NO, because the rule killed
    on any place it did not recognise. "Based in Al Barsha" is a Dubai coach
    telling us exactly where they are."""
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


# ----------------------------------- the bridge from observations to the floor


def _obs(days_ago, url="https://linkedin.com/posts/x"):
    return {"url": url,
            "published_at": (TODAY - timedelta(days=days_ago)).isoformat()}


def test_a_fresh_observation_settles_the_floor():
    """F3: the floor's evidence has existed since P1 and nothing read it. A
    research worker returns dated observations before it calls this floor."""
    seen, why = q.activity_from_observations([_obs(40), _obs(6)], today=TODAY)
    assert seen == TODAY - timedelta(days=6)
    assert "linkedin.com/posts/x" in why
    assert q.check_active(last_seen=seen, today=TODAY).value == q.YES


def test_a_stale_observation_set_is_indistinguishable_from_none():
    """**The safety property of the whole change.** `check_active` returns NO
    for a stale date, so handing it the newest of an old set would open a brand
    new kill surface at the one floor built not to have one — on the weakest
    possible evidence, that the pages we happened to retrieve were old. D4 says
    a false kill is permanent and invisible; better evidence is not a reason to
    weaken that."""
    stale, why = q.activity_from_observations([_obs(200), _obs(400)], today=TODAY)
    none_at_all, _ = q.activity_from_observations([], today=TODAY)
    assert stale is none_at_all is None
    assert q.check_active(last_seen=stale, today=TODAY).value == q.UNCLEAR
    # It still says what it saw, because that is worth reading in a report.
    assert "too old to settle the floor, and never a kill" in why


def test_a_single_stale_date_is_also_indistinguishable_from_none():
    """The second route to `check_active`, which had no such guard.

    `activity_from_observations` was the only thing applying the upward-only
    rule, and `cmd_qualify` reached the floor another way: a research object's
    own `last_activity` field went straight through. On `2026-08-03-icf1` that
    killed 9 of 62 leads whose workers had recorded `active_recent: unclear`
    beside a real older date — the floor overriding a worker's own verdict with
    a harsher one derived from that worker's own evidence.
    """
    stale, why = q.activity_within_window(TODAY - timedelta(days=65), today=TODAY)
    assert stale is None
    assert q.check_active(last_seen=stale, today=TODAY).value == q.UNCLEAR
    assert "never a kill" in why


def test_a_fresh_single_date_still_settles_the_floor_upward():
    fresh, why = q.activity_within_window(TODAY - timedelta(days=3), today=TODAY)
    assert fresh == TODAY - timedelta(days=3)
    assert q.check_active(last_seen=fresh, today=TODAY).value == q.YES
    assert "3d ago" in why


def test_a_future_single_date_is_not_a_kill_either():
    when, why = q.activity_within_window(TODAY + timedelta(days=5), today=TODAY)
    assert when is None
    assert "future" in why


def test_no_date_at_all_reads_as_no_date():
    assert q.activity_within_window(None, today=TODAY)[0] is None


def test_somebody_elses_post_about_them_never_settles_the_floor():
    """Found on the first batch that used this. A lead's only dated observation
    was a company post naming her, two days old, and this called her active on
    it. The floor asks whether SHE was active. `select` excludes `third_party`
    one stage over for the same reason (ban #7), and the floor wanting different
    evidence from the hook was never the intent."""
    theirs = dict(_obs(2), author="third_party")
    assert q.activity_from_observations([theirs], today=TODAY)[0] is None
    # And it cannot cause a kill — removing evidence only moves toward unclear.
    assert q.check_active(last_seen=None, today=TODAY).value == q.UNCLEAR


def test_unknown_authorship_still_counts():
    """`unknown` is the dataclass default and means no tell was available, not
    that the tell said no — resolve's rule, applied here. Filtering it out would
    reject most of a real pool for a field nobody was required to fill."""
    seen, _ = q.activity_from_observations(
        [dict(_obs(3), author="unknown")], today=TODAY)
    assert seen == TODAY - timedelta(days=3)


def test_a_fresh_own_post_outranks_a_fresher_third_party_one():
    """The third-party item is dropped, not merely outranked — otherwise a
    lead's own stale post would lose to somebody else's fresh one."""
    seen, why = q.activity_from_observations(
        [dict(_obs(1), author="third_party"), dict(_obs(9), author="self")],
        today=TODAY)
    assert seen == TODAY - timedelta(days=9)


def test_the_window_boundary_holds_for_observations_too():
    seen, _ = q.activity_from_observations([_obs(30)], today=TODAY)
    assert seen == TODAY - timedelta(days=30)
    assert q.activity_from_observations([_obs(31)], today=TODAY)[0] is None


def test_a_malformed_published_at_is_skipped_not_fatal():
    """The schema gate's job, not this one's. A worker writing `null` is being
    honest and must not surface here as a crash."""
    seen, _ = q.activity_from_observations(
        [{"url": "u", "published_at": "last Tuesday"},
         {"url": "u", "published_at": None},
         {"url": "u"},
         _obs(3)], today=TODAY)
    assert seen == TODAY - timedelta(days=3)


def test_a_future_observation_is_ignored():
    """A date nobody could have read is a date nobody fetched. It must not
    become the newest and settle the floor."""
    future = {"url": "u", "published_at": (TODAY + timedelta(days=5)).isoformat()}
    assert q.activity_from_observations([future], today=TODAY)[0] is None
    seen, _ = q.activity_from_observations([future, _obs(4)], today=TODAY)
    assert seen == TODAY - timedelta(days=4)


def test_observations_may_be_objects_as_well_as_dicts():
    from outbound.observe import Observation
    obs = Observation(url="https://x.ae/post", published_at=(TODAY - timedelta(days=2)).isoformat())
    seen, _ = q.activity_from_observations([obs], today=TODAY)
    assert seen == TODAY - timedelta(days=2)


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
    """A real case: their site read Life/Mindset while their LinkedIn headline said
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


# ------------------------------------------------- the lists that must agree


def test_the_coach_types_qualify_assigns_are_the_ones_research_accepts():
    """`qualify` picks a coach type and `research` carries it, so the two lists
    are the same list written twice. Nothing but this reads them together.

    `research` adds `""` for not-yet-known. That is the only legal difference —
    a segment in one and not the other means `qualify` can assign a type its own
    schema check rejects, or a type exists that nothing can ever assign.
    """
    assert set(r.COACH_TYPES) - {""} == set(q.COACH_TYPES)


def test_the_copy_bank_targets_the_same_segments_with_any_for_the_generic_pool():
    """`copy_sync`'s list is deliberately NOT the same list, and this pins the
    difference so it stays deliberate.

    A lead HAS a coach type; an identity line TARGETS one. So the line side
    swaps `Other` for `Any`, the generic pool every unknown-segment lead draws
    from. Without this, dropping `Any` reads as a tidy-up and silently empties
    the pool those leads fall back to.
    """
    from outbound import copy_sync

    assert (set(copy_sync.COACH_TYPES)
            == (set(q.COACH_TYPES) - {"Other"}) | {"Any"})


def test_sells_to_is_one_list_the_crm_owns_plus_two_declared_extras():
    """Three modules, three different member sets, all derived from the CRM's.

    `research` adds `""` (not collected — it is never inferred, so this is
    common). `copy_sync` adds `""` and `any`, a line that fits either audience.
    Both are additions; neither may drop or rename a value the CRM has.
    """
    from audit import airtable
    from outbound import copy_sync

    assert set(r.SELLS_TO) == set(airtable.SELLS_TO) | {""}
    assert set(copy_sync.SELLS_TO) == set(airtable.SELLS_TO) | {"", "any"}


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


# ------------------------------------------------- the floors, after the batch
#
# Every case below is a real row from the 155-lead run that a worker had to
# hand-override with sourced evidence, or a real false pass nobody caught.


def test_is_coach_can_finally_say_no():
    """It was documented as a hard floor and had three returns, none of which
    could be NO. It substring-matched the word "coach" and nothing else."""
    for headline in ("Cabin crew at flydubai",
                     "Retail Supervisor at Bacardi",
                     "Lecturer in Business, Middlesex University Dubai"):
        assert q.check_coach(headline=headline).value == q.NO, headline


def test_is_coach_needs_all_three_conditions_to_say_no():
    """A stated other occupation AND no coach word AND no offer. Plenty of real
    coaches also have a day job, and a false kill is permanent."""
    assert q.check_coach(headline="Nurse and wellness coach").value == q.YES
    assert q.check_coach(
        headline="Nurse", text="Book a discovery call. My clients get 1:1 sessions."
    ).value == q.UNCLEAR


def test_is_coach_matches_on_word_boundaries():
    """`"coach" in haystack` fires on coachella, stagecoach, and any URL with
    the letters in it — which is how a floor comes to pass everything."""
    assert q.check_coach(text="I went to Coachella last year.").value == q.UNCLEAR


def test_a_coaching_offer_with_no_coach_word_is_unclear_not_no():
    v = q.check_coach(text="Book a session with me. Packages start in September.")
    assert v.value == q.UNCLEAR and "no coach word" in v.evidence


def test_a_hobby_mention_still_passes_and_that_is_deliberate():
    """The airline CEO whose goalie coaching is a weekend thing. Telling that
    apart from "I coach founders" needs context this function does not have,
    and getting it wrong costs a real lead permanently."""
    assert q.check_coach(headline="CEO",
                         text="At weekends I do some goalie coaching.").value == q.YES


def test_a_location_sentence_about_a_past_employer_does_not_kill():
    """The real false kill: "based in Singapore" described a former employer."""
    v = q.check_uae(text="Leadership coach in Dubai. Previously at Acme, "
                         "based in Singapore.")
    assert v.value == q.YES


def test_a_location_sentence_about_a_client_does_not_kill():
    assert q.check_uae(
        text="Our client, based in London, doubled their revenue."
    ).value != q.NO


def test_a_third_person_location_does_not_kill():
    assert q.check_uae(text="She is based in Toronto and runs the studio."
                       ).value != q.NO


def test_a_plain_bio_line_still_kills():
    """The default has to stay "this is about them" — "Based in Manchester."
    with no pronoun is the ordinary bio form, and requiring a first person
    would spare every one of them."""
    assert q.check_uae(text="Based in Manchester, working worldwide.").value == q.NO


def test_their_own_location_field_outranks_the_page():
    """Two claims about where one person is. The field is the one that is
    definitely about them."""
    assert q.check_uae(city="Dubai", text="Based in Singapore.").value == q.YES


def test_a_uae_city_in_a_location_field_settles_it():
    assert q.check_uae(location="Dubai, United Arab Emirates").value == q.YES


def test_the_two_letter_shorthands_are_gone():
    """`ad` and `ae` carried no signal a real bio would ever intend."""
    assert "ad" not in q.UAE_SHORTHAND and "ae" not in q.UAE_SHORTHAND


def test_scale_alone_no_longer_pulls_a_fitness_coach_into_business():
    """It did, twice, on the first batch. `\\b` binds only to the first branch
    of an alternation, so `scale` was matching bare."""
    kind, _ = q.classify_coach_type(
        site_text="Strength and fitness coach. I help people scale their training.")
    assert kind == "Fitness"


def test_scaling_a_business_still_reads_as_business():
    kind, _ = q.classify_coach_type(
        site_text="I help you scale your business past AED 1m.")
    assert kind == "Business"


def test_wellness_in_passing_no_longer_makes_a_brand_strategist_a_health_coach():
    kind, _ = q.classify_coach_type(
        site_text="Brand strategist for the wellness industry.")
    assert kind == ""


def test_a_real_wellness_coach_still_reads_as_health():
    kind, _ = q.classify_coach_type(
        site_text="Wellness coach helping women sleep better.")
    assert kind == "Health"
