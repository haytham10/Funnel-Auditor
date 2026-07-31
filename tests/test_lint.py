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
