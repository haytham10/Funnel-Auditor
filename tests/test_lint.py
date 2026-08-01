"""The linter is the only thing standing between a model and the upload file.

Run: python -m pytest tests/test_lint.py -q
 or: python tests/test_lint.py

Every check gets a red-team case: an email built to violate exactly one rule,
which must fail with the right message and for the right reason. A linter that
passes everything is indistinguishable from no linter, and the way that happens
in practice is a regex that quietly stops matching.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from outbound import anchors, lint

# Derived from the real fact table rather than hardcoded, so a change to
# copy/results.csv shows up here instead of silently diverging from it.
FACTS = anchors.load_facts()
HEALTH_NUMBERS = anchors.all_numbers(FACTS)


def good_beats():
    return {
        "hook": ("You wrote that you couldn't contain the excitement of "
                 "uncovering a solution for yourself."),
        "identity": ("My job is finding your next client. A health coach in "
                     "Dubai closed AED 78,000 over 2 months from prospects I "
                     "put in front of them."),
        "offer": ("I pulled 10 names for you before writing this. Not a "
                  "scraped list, people I'd actually start with."),
        "cta": ("15 minutes and they're yours the same day. I'll tell you why "
                "these 10 and not the other 40."),
        # NOT ps-01 ("not a list"): the offer beat above already says
        # "Not a scraped list", and check_echo rejects that pair.
        "ps": "ps: a no here costs you nothing and costs me nothing.",
    }


def body_from(beats, name="Sarah"):
    from outbound.export import assemble_body
    return assemble_body(beats, greeting_name=name)


def run(beats=None, subject="your Hashimoto post", allowed=None, name="Sarah"):
    beats = beats or good_beats()
    return lint.check_email(
        name=name, subject=subject, body=body_from(beats),
        beats=beats, allowed_numbers=allowed or HEALTH_NUMBERS, facts=FACTS)


# ------------------------------------------------------------------- baseline


def test_a_clean_email_passes():
    result = run()
    assert result.passed, result.failures


# -------------------------------------------------------------- traceability


def test_invented_number_fails():
    beats = good_beats()
    beats["identity"] = ("My job is finding your next client. A health coach "
                         "in Dubai closed AED 91,500 from prospects I put in "
                         "front of them.")
    result = run(beats)
    assert not result.passed
    assert any("91,500" in f for f in result.failures)


def test_number_relabelled_onto_a_named_segment_fails():
    """120,000 is real, but it is Business's. Attached to a sentence that says
    "health coach", it is a relabel — the exact thing that surfaces when two
    coaches compare emails."""
    beats = good_beats()
    beats["identity"] = ("My job is finding your next client. A health coach "
                         "in Dubai closed AED 120,000 from prospects I put in "
                         "front of them.")
    result = run(beats)
    assert not result.passed
    assert any("120,000" in f for f in result.failures)


def test_an_ordinal_is_a_date_not_a_claim():
    """"the 21st of June" tripped traceability, because 21 is not in anyone's
    fact table. An ordinal is never a result — it is a day, a place in a queue
    or a floor number, and none of those are claims about client outcomes."""
    beats = good_beats()
    beats["hook"] = ("Caught your talk on the 21st of June about pricing "
                     "packages, and the 3rd point landed.")
    result = run(beats)
    assert result.passed, result.failures


def test_a_cardinal_number_is_still_caught_next_to_an_ordinal():
    """The ordinal strip must not blind the check to real digits around it."""
    beats = good_beats()
    beats["identity"] = ("My job is finding your next client. On the 21st I "
                         "put AED 91,500 in front of a coach here.")
    result = run(beats)
    assert not result.passed
    assert any("91,500" in f for f in result.failures)


def test_spelled_out_number_is_checked_too():
    """"eleven" is not a meeting count, a client count or a period anywhere in
    the fact table. Spelled out or in digits, it is the same invention."""
    beats = good_beats()
    beats["offer"] = ("I pulled eleven names for you before writing this. Not "
                      "a scraped list, people I'd actually start with.")
    result = run(beats)
    assert not result.passed
    assert any("eleven" in f for f in result.failures)


def test_widening_another_segments_result_is_allowed():
    """One of the three sanctioned ways to vary: drop the segment, keep
    "coaches here". True of every lead, and weaker than an exact match but far
    stronger than a wrong one. `id-corp-1` in the live file does exactly this."""
    beats = good_beats()
    beats["identity"] = ("Your next client is the whole job. I got a coach here "
                         "12 meetings in 60 days, and 5 of them signed.")
    result = run(beats)
    assert result.passed, result.failures


def test_k_suffix_resolves_to_the_same_value():
    beats = good_beats()
    beats["identity"] = ("My job is finding your next client. A health coach "
                         "in Dubai closed AED 78k from prospects I put in "
                         "front of them.")
    assert run(beats).passed


# ---------------------------------------------------------- claim preservation


def test_offer_that_lost_its_ten_names_fails():
    beats = good_beats()
    beats["offer"] = "I put a shortlist together for you before writing this."
    result = run(beats)
    assert not result.passed
    assert any("offer beat lost its claim" in f for f in result.failures)


def test_cta_without_the_clock_fails():
    beats = good_beats()
    beats["cta"] = "15 minutes and I'll tell you why these 10 and not the other 40."
    result = run(beats)
    assert not result.passed
    assert any("clock" in f for f in result.failures)


def test_cta_without_the_why_these_ten_half_fails():
    """Reply-to-call went 0-for-9 when the call held nothing that couldn't be
    typed in an email. The second half of the close is load-bearing."""
    beats = good_beats()
    beats["cta"] = "15 minutes and they're yours the same day."
    result = run(beats)
    assert not result.passed
    assert any("why these ten" in f for f in result.failures)


def test_missing_ps_fails():
    beats = good_beats()
    beats["ps"] = ""
    result = run(beats)
    assert not result.passed
    assert any("ps beat is missing" in f for f in result.failures)


# ------------------------------------------------------------- beat collisions


def test_the_offer_and_ps_cannot_both_say_list():
    """Found by a cold reader on a real draft, not by any check. `b4-01` says
    "Not a scraped list" and `ps-01` says "not a list"; four lines apart in
    ninety words the same denial twice reads as protesting too much. Neither
    line is at fault, which is why this is checked on the PAIR."""
    beats = good_beats()
    beats["ps"] = "ps: not a list. If the timing's wrong that's a fine answer."
    result = run(beats)
    assert not result.passed
    assert any("both say 'list'" in f for f in result.failures)


def test_a_shared_word_in_the_authored_beats_is_not_a_collision():
    """Only the three library-drawn beats are checked. The hook and identity
    beat are authored per lead, so a repeat there is the drafter's own doing
    and the voice rules already cover it."""
    beats = good_beats()
    beats["hook"] = "You wrote about the list of things nobody says out loud."
    assert run(beats).passed, run(beats).failures


# ---------------------------------------------------------------- the bridge


def test_bare_stat_identity_fails():
    """22 of 31 identity lines opened on a bare stat. A hook followed by a
    naked number is two unrelated paragraphs."""
    beats = good_beats()
    beats["identity"] = ("9 meetings in 6 weeks for the last health coach I "
                         "worked with in Dubai, and 6 of them signed.")
    result = run(beats)
    assert not result.passed
    assert any("before it turns to the reader" in f for f in result.failures)


def test_second_person_after_the_number_still_fails():
    beats = good_beats()
    beats["identity"] = ("9 meetings in 6 weeks for a health coach in Dubai, "
                         "which is the kind of thing your practice could use.")
    result = run(beats)
    assert not result.passed


def test_gendered_pronoun_in_identity_fails():
    beats = good_beats()
    beats["identity"] = ("My job is finding your next client. A health coach "
                         "in Dubai closed AED 78,000 from prospects I put in "
                         "front of her.")
    result = run(beats)
    assert not result.passed
    assert any("gendered pronoun" in f for f in result.failures)


# ------------------------------------------------------------------- the voice


def test_em_dash_fails():
    beats = good_beats()
    beats["hook"] = "You wrote about your diagnosis — that stuck with me."
    result = run(beats)
    assert not result.passed
    assert any("em-dash" in f for f in result.failures)


def test_operator_jargon_fails():
    beats = good_beats()
    beats["hook"] = "I was looking at your funnel and something stood out to me."
    result = run(beats)
    assert not result.passed
    assert any("jargon" in f for f in result.failures)


def test_weak_closer_fails():
    beats = good_beats()
    beats["ps"] = "ps: no pressure either way, and nothing to unsubscribe from."
    result = run(beats)
    assert not result.passed
    assert any("weak closer" in f for f in result.failures)


def test_missing_sign_off_fails():
    beats = good_beats()
    body = "\n\n".join([beats["hook"], beats["identity"], beats["offer"],
                        beats["cta"], beats["ps"]])
    result = lint.check_email(name="Sarah", subject="your post", body=body,
                              beats=beats, allowed_numbers=HEALTH_NUMBERS,
                              facts=FACTS)
    assert not result.passed
    assert any("sign-off" in f for f in result.failures)


def test_bare_link_fails():
    beats = good_beats()
    beats["cta"] = ("15 minutes and they're yours the same day, book at "
                    "calendly.com/haytham. I'll tell you why these 10 and not "
                    "the other 40.")
    result = run(beats)
    assert not result.passed
    assert any("bare link" in f for f in result.failures)


def test_unformatted_number_fails():
    beats = good_beats()
    beats["identity"] = ("My job is finding your next client. A health coach "
                         "in Dubai closed AED 78000 from prospects I put in "
                         "front of them.")
    result = run(beats)
    assert not result.passed
    assert any("merge field" in f for f in result.failures)


def test_over_long_email_fails():
    beats = good_beats()
    beats["hook"] = beats["hook"] + " " + ("It really did land with me and I " * 12)
    result = run(beats)
    assert not result.passed
    assert any("over 95" in f for f in result.failures)


def test_too_short_email_fails():
    beats = {"hook": "Saw your post.", "identity": "Your next client is my job. 9 meetings.",
             "offer": "I found 10 names already.",
             "cta": "15 minutes, yours the same day, and why these 10 not the other 40.",
             "ps": "ps: a no here costs you nothing."}
    result = run(beats)
    assert not result.passed
    assert any("under 67" in f for f in result.failures)


# --------------------------------------------------------------------- subject


def test_long_subject_fails():
    result = run(subject="a quick note about the post you wrote on your diagnosis")
    assert not result.passed
    assert any("over 8" in f for f in result.failures)


def test_empty_subject_fails():
    result = run(subject="")
    assert not result.passed


def test_empty_body_fails_without_crashing():
    result = lint.check_email(name="Sarah", subject="hi", body="",
                              beats={}, allowed_numbers=HEALTH_NUMBERS,
                              facts=FACTS)
    assert not result.passed
    assert result.failures == ["body is empty"]


# ------------------------------------------------------------------- the batch


def _email(subject, identity, opening="Saw the piece you wrote last week."):
    beats = good_beats()
    beats["identity"] = identity
    beats["hook"] = opening
    return {"subject": subject, "body": body_from(beats), "beats": beats}


def test_batch_flags_an_overused_fixed_line():
    emails = [_email(f"subject {i}", "Your next client is my job. 9 meetings.",
                     opening=f"Your {i} post landed with me.")
              for i in range(10)]
    result = lint.check_batch(emails, {"offer": {"b4-01": 0.5}})
    assert not result.passed
    assert any("b4-01" in f for f in result.failures)


def test_a_small_batch_reports_repetition_without_failing():
    """With four offer lines and three emails, two drawing the same line is
    67% and means nothing. Enforcing a percentage there would fail every small
    batch and teach everyone to ignore the check."""
    emails = [_email(f"subject {i}", "Your next client is my job. 9 meetings.",
                     opening=f"Your {i} post landed with me.")
              for i in range(3)]
    result = lint.check_batch(emails, {"offer": {"b4-01": 0.67}})
    assert result.passed
    assert any("b4-01" in w for w in result.warnings)


def test_batch_flags_a_reused_subject():
    """A reused subject fails at any batch size — it is not a percentage."""
    emails = [_email("same subject", "Your next client is my job. 9 meetings."),
              _email("same subject", "Your next client is my job. 8 meetings.")]
    result = lint.check_batch(emails)
    assert not result.passed
    assert any("reused" in f for f in result.failures)


def test_batch_flags_a_repeated_opening_shape():
    emails = [_email(f"subject {i}", "Your next client is my job. 9 meetings.",
                     opening="Saw the piece you wrote last week.")
              for i in range(10)]
    result = lint.check_batch(emails)
    assert not result.passed
    assert any("open on" in f for f in result.failures)


def test_batch_warns_on_a_collapsed_bridge_phrase():
    """5 of 9 bridging lines opened 'My job is finding your next client.'
    verbatim, which at 43 sends lands in one inbox in six."""
    emails = [_email(f"subject {i}",
                     "My job is finding your next client. A coach here closed "
                     "AED 78,000.",
                     opening=f"Saw the {i} piece you wrote recently.")
              for i in range(10)]
    result = lint.check_batch(emails)
    assert any("My job is finding" in w.lower() or "my job is finding" in w
               for w in result.warnings)


def test_a_varied_batch_passes():
    identities = [
        "Your next client is the job. A coach here closed AED 78,000.",
        "Finding you a client is what I do. 9 meetings in 6 weeks.",
        "You'd want the meetings, not the followers. 6 of 9 signed.",
    ]
    emails = [_email(f"subject {i}", identity, opening=f"Your {i} post landed.")
              for i, identity in enumerate(identities)]
    result = lint.check_batch(emails)
    assert result.passed, result.failures


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


# ------------------------------------------------- the identity claim
#
# The identity beat is the one beat the drafter WRITES. These pin both halves
# of that: the sentence is free, the claim is not. The load-bearing one is
# `test_a_sentence_sharing_no_words_with_the_reference_still_passes` — without
# it, any of the checks below could quietly re-impose the verbatim rule.


def _claim(raw):
    return anchors.claim_for(anchors.Line("x", "", {"claim": raw}), FACTS)


def test_a_sentence_sharing_no_words_with_the_reference_still_passes():
    """The whole point. `id-biz-3`'s reference is "12 meetings for the last
    business coach I worked with in Dubai, and 5 of them turned into clients."
    A completely different sentence making the same claim must pass, because
    otherwise the drafter cannot fix a defective line and the lead holds."""
    spec = _claim("Business:meetings,clients,city")
    written = ("Your next client is the whole job for me. The most recent business "
               "coach I did this for, here in Dubai, sat down with 12 people and "
               "signed 5.")
    assert lint.check_identity_claim(written, spec) == []


def test_a_sentence_that_drops_a_required_figure_fails():
    spec = _claim("Business:meetings,period,clients")
    problems = lint.check_identity_claim(
        "I booked a business coach 12 meetings and 5 of them signed.", spec)
    assert any("period = 60 days" in p for p in problems)


def test_the_real_id_fit_2_defect_is_caught():
    """It shipped for a month. "closed AED 36k in 6 weeks" against a Fitness
    row whose close_period is 45 days, passing only because 6 is in
    OFFER_NUMBERS — which is why a claim licenses its own figures and not
    those."""
    spec = _claim("Fitness:aed_closed,close_period,city")
    problems = lint.check_identity_claim(
        "I find your next paying client, just like I did with a fitness coach in "
        "Dubai who closed AED 36k in 6 weeks.", spec)
    assert any("close_period = 45 days" in p for p in problems)
    assert any('cites "6"' in p for p in problems)


def test_an_offer_number_is_not_licensed_in_the_identity_beat():
    spec = _claim("Life:meetings,clients")
    problems = lint.check_identity_claim(
        "I got a life coach 8 meetings, 3 signed, and 10 names are next.", spec)
    assert any('cites "10"' in p for p in problems)


def test_a_period_restated_in_another_exact_unit_passes():
    # 60 days and 2 months are the same fact. A gate that knows only one of
    # them rejects an honest sentence, which is how drafters learn to route
    # around a gate.
    spec = _claim("Business:period")
    assert lint.check_identity_claim(
        "Your equivalent, a business coach, got 2 months of this.", spec) == []
    assert lint.check_identity_claim(
        "Your equivalent, a business coach, got 60 days of this.", spec) == []


def test_a_bare_number_does_not_satisfy_a_period_that_needs_its_unit():
    # Otherwise "2 of them signed" would silently satisfy a 60-day claim, and
    # the check would pass a sentence that says nothing about the timeframe.
    spec = _claim("Business:period")
    assert lint.check_identity_claim("2 of them signed for you.", spec) != []


def test_the_article_form_of_one_unit_counts():
    # "inside a week" carries no digit at all, and `id-lead-3` is written that
    # way. "in a month" is `id-fit-1`.
    assert lint.check_identity_claim(
        "Your leadership coach equivalent had their first meeting inside a week.",
        _claim("Leadership:first_meeting_days")) == []
    assert lint.check_identity_claim(
        "For you, like the fitness coach before you: 7 meetings in a month.",
        _claim("Fitness:meetings,period")) == []


def test_week_one_satisfies_a_seven_day_first_client():
    assert lint.check_identity_claim(
        "Your equivalent, a mindset coach, landed their first client in week 1.",
        _claim("Mindset:first_client_days")) == []


def test_every_one_is_prose_and_not_a_figure():
    # `id-biz-2` and `id-exec-1` both say "every one with somebody who could
    # sign off". Reading that `one` as a figure fails two good lines.
    spec = _claim("Business:meetings,clients")
    assert lint.check_identity_claim(
        "I booked a business coach 12 meetings, every one with somebody who could "
        "sign off, and 5 signed.", spec) == []


def test_a_segment_scoped_claim_needs_its_segment_noun():
    spec = _claim("Health:meetings,clients")
    assert any("health coach" in p for p in lint.check_identity_claim(
        "I got someone 9 meetings and 6 of them signed.", spec))


def test_a_widened_claim_must_not_name_a_segment():
    # Not because it would be false — they ARE Health's figures. Because a
    # widened line is dealt across segments, so a named reference group is a
    # mismatch for most of the people who get it.
    spec = _claim("Health:meetings,clients|widened")
    problems = lint.check_identity_claim(
        "I did this for a health coach who closed 6 of the 9 meetings I set up.", spec)
    assert any("dealt across segments" in p for p in problems)
    assert lint.check_identity_claim(
        "I did this for a coach here who closed 6 of the 9 meetings I set up.",
        spec) == []


def test_the_wrong_city_fails():
    # Nothing catches this today: `check_attribution` only looks at numbers, so
    # "a life coach in Dubai" would sail through while the Life row says Abu
    # Dhabi.
    spec = _claim("Life:meetings,city")
    assert any("Abu Dhabi" in p for p in lint.check_identity_claim(
        "I got a life coach in Dubai 8 meetings.", spec))
    assert lint.check_identity_claim(
        "I got a life coach in Abu Dhabi 8 meetings.", spec) == []


def test_a_city_the_claim_never_declared_fails():
    # Keyed on what the line DECLARED, not on whether its row has a city —
    # every row does. `id-career-3` cites Career's meetings and period and
    # deliberately says "here" rather than Dubai; naming the city would be an
    # undeclared claim, and `check_attribution` only ever looks at numbers.
    spec = _claim("Career:meetings,period")
    assert any("does not assert" in p for p in lint.check_identity_claim(
        "12 meetings in 45 days for a career coach in Dubai.", spec))
    assert lint.check_identity_claim(
        "12 meetings in 45 days for a career coach here.", spec) == []


def test_a_retention_claim_needs_the_retention_said_out_loud():
    spec = _claim("Executive:meetings,still_working")
    assert lint.check_identity_claim(
        "6 meetings for an executive coach, and I'm still working with them.",
        spec) == []
    assert lint.check_identity_claim(
        "6 meetings for an executive coach.", spec) != []


def test_a_missing_claim_is_reported_rather_than_skipped():
    problems = lint.check_identity_claim("anything at all", None)
    assert problems and "no claim spec" in problems[0]


def test_check_email_warns_when_no_claim_was_passed():
    # A check that quietly does not run is worse than one that is not there,
    # because the PASS line looks the same either way.
    result = lint.check_email(
        name="x", subject="A subject here", body="body text",
        beats={"identity": "x"}, allowed_numbers=set())
    assert any("claim spec" in w for w in result.warnings)


def test_every_live_bank_line_satisfies_its_own_claim():
    """The regression that matters most. If a bank line cannot pass the check
    its own Claim implies, every email dealt that line fails, and the drafter
    is asked to satisfy something impossible."""
    bank = anchors.CopyBank.from_csv()
    broken = {
        line.id: lint.check_identity_claim(line.line, anchors.claim_for(line, FACTS))
        for line in bank.identity
    }
    assert not {k: v for k, v in broken.items() if v}
