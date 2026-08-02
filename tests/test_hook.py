"""The hook proposal gate: everything mechanical, before a verifier is spent.

Run: python -m pytest tests/test_hook.py -q
 or: python tests/test_hook.py

F4 named the hook as the only consequential artifact with no mechanical gate.
The consequence, measured: **six of twelve drafts on `2026-08-01-q1` had to
alter text an independent verifier had certified word for word.** An em-dash,
spaced hyphens, "touchpoints" off the jargon list, and four figures — every one
a rule the linter had always held and the hook stage had never run.

That is F11's shape: a constraint applied after the point where honouring it was
free. When a quote breaks a voice rule the honest repair is to pick a DIFFERENT
quote, and only the worker can do that. One stage later the drafter has neither
the alternatives nor the authority, so it edits the citation instead — and a
hook squeezed after certification is a citation drifting from its source.

**Nothing here verifies anything**, and a test says so: the live re-fetch is the
only mechanism that has ever caught a fabricated claim.
"""

import os
import sys
import tempfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("OUTBOUND_LEDGER_ROOT",
                      tempfile.mkdtemp(prefix="outbound-ledger-"))

from outbound import hook

TODAY = date(2026, 8, 1)

WORKING_URL = ("https://www.linkedin.com/posts/lucycrussell_i-put-my-phone-on-"
               "airplane-mode-10-days-ago-activity-7356")


def proposal(**overrides) -> hook.HookProposal:
    fields = {
        "lead_key": "lucy@x.ae",
        "quote": "I put my phone on airplane mode 10 days ago and left it there",
        "line": "and you wrote it up the week you were still doing it",
        "hook_type": "LIFE",
        "source_url": WORKING_URL,
        "published_at": "2026-07-20",
    }
    fields.update(overrides)
    return hook.HookProposal(**fields)


# ------------------------------------------------------------------- baseline


def test_a_real_proposal_passes():
    assert hook.validate(proposal(), today=TODAY) == []


def test_a_hook_with_no_clause_is_the_failure_the_rules_call_no_writer_in_it():
    """"The hook must have a writer in it" is ban #9 and the most common failure
    of the twelve. A quote handed back with nothing taken from it produces an
    identity beat that reads as a non sequitur, whatever that beat says."""
    problems = hook.validate(proposal(line=""), today=TODAY)
    assert any("no writer in it" in p for p in problems), problems


def test_a_hook_with_no_quote_is_not_a_hook():
    assert any("no quote" in p for p in hook.validate(proposal(quote=""),
                                                      today=TODAY))


# ---------------------------------------------------------------- the citation


def test_a_linkedin_post_url_with_an_empty_slug_is_unusable():
    """harvestapi builds post URLs from a text-derived slug, and a post with no
    usable text gets an empty one. Maurice Hellemons' hook was REFUTED on this:
    the content was real and paid for, and the URL 404s.

    An email cannot cite a page the reader cannot open, so it is unusable
    however true the quote is — and it costs a full verifier pass to find out
    any later than here."""
    dead = "https://www.linkedin.com/posts/mauricehellemons_-activity-7356"
    assert "empty slug" in hook.unusable_citation(dead)
    assert hook.unusable_citation(WORKING_URL) == ""


def test_a_missing_or_unfetchable_url_is_named_differently():
    """"no citation" and "a citation nobody can open" are different repairs."""
    assert "no source_url" in hook.unusable_citation("")
    assert "not a fetchable URL" in hook.unusable_citation("linkedin.com/in/x")


def test_a_hook_with_no_date_cannot_be_shown_to_be_recent():
    problems = hook.validate(proposal(published_at=""), today=TODAY)
    assert any("published_at" in p for p in problems)


def test_a_future_date_is_a_date_nobody_fetched():
    problems = hook.validate(proposal(published_at="2026-09-01"), today=TODAY)
    assert any("future" in p for p in problems)


# -------------------------------------------------------------------- the voice


def test_an_em_dash_in_the_quote_is_caught_before_certification():
    """`check_voice` refuses an em-dash absolutely, and it did so three stages
    after a verifier had certified the exact wording carrying it."""
    problems = hook.validate(proposal(quote="we cut it down — hard, that week"),
                             today=TODAY)
    assert any("em-dash" in p for p in problems), problems


def test_jargon_in_the_quote_is_caught_too():
    problems = hook.validate(
        proposal(quote="we cut the touchpoints down that quarter"), today=TODAY)
    assert any("touchpoints" in p for p in problems), problems


def test_every_voice_finding_says_pick_a_different_quote():
    """The repair a worker must NOT make is editing the recipient's words. A
    gate that offered a fixed string would be inviting exactly that."""
    problems = hook.validate(proposal(quote="we cut it down — hard, that week"),
                             today=TODAY)
    voice = [p for p in problems if "em-dash" in p]
    assert voice and all("do NOT edit their words" in p for p in voice)


def test_the_fragment_rules_are_the_linters_own_and_not_a_second_copy():
    """`check_voice` calls `check_voice_fragment`. A hook has no sign-off, no
    paragraph count and no word budget of its own, so only those stay behind."""
    from outbound import lint

    assert lint.check_voice_fragment("we cut it — hard") == \
        [p for p in lint.check_voice("we cut it — hard")[0] if "em-dash" in p]


# ------------------------------------------------------------------- the joins


def test_a_blank_observation_id_is_legal_with_no_shortlist_to_check_against():
    """The single-lead repair path in `outbound-draft` has no batch behind it,
    so the join check is opt-in. A batch run passes `--against`."""
    assert hook.validate(proposal(observation_id=""), today=TODAY) == []


# --------------------------------------------------------------------- the join


OBS_TEXT = ("I put my phone on airplane mode 10 days ago and left it there. "
            "The first three days were genuinely unpleasant.")


def shortlists(text: str = OBS_TEXT, obs_id: str = "abc123") -> dict:
    return {"lucy@x.ae": [{"obs_id": obs_id, "quote": text, "rank": 1}]}


def test_a_verbatim_quote_from_the_named_observation_passes():
    """Ban #3 — "no invented specifics" — was a sentence an agent was asked to
    remember, for as long as there was nothing to check it against. `select`
    hands the worker the observation's text, so now there is."""
    got = hook.validate(proposal(observation_id="abc123"), today=TODAY,
                        shortlists=shortlists())
    assert got == [], got


def test_a_quote_that_drifted_by_one_word_is_caught():
    """Every way this fails downstream is the same way: the verifier refutes a
    citation this stage has already paid to produce."""
    edited = proposal(observation_id="abc123",
                      quote="I put my phone on airplane mode 10 days ago and "
                            "kept it there")
    got = hook.validate(edited, today=TODAY, shortlists=shortlists())
    assert any("not a contiguous piece" in p for p in got), got


def test_two_sentences_fused_into_one_quote_is_caught():
    """A real refusal from `2026-08-01-q1`: a hook that welded two separate
    sentences together read perfectly and was not on the page in that form."""
    fused = proposal(observation_id="abc123",
                     quote="I put my phone on airplane mode 10 days ago. The "
                           "first three days were genuinely unpleasant.")
    got = hook.validate(fused, today=TODAY, shortlists=shortlists())
    assert any("not a contiguous piece" in p for p in got), got


def test_line_breaks_do_not_count_as_drift():
    """A scraped post carries newlines the quote will not. Whitespace is the one
    thing that legitimately differs; case and punctuation are not, because a
    comparison that forgave a changed word would forgive the drift it exists to
    catch."""
    wrapped = shortlists("I put my phone on airplane mode\n10 days ago and left "
                         "it there.")
    got = hook.validate(
        proposal(observation_id="abc123",
                 quote="I put my phone on airplane mode 10 days ago and left it "
                       "there"),
        today=TODAY, shortlists=wrapped)
    assert got == [], got


def test_an_observation_id_outside_the_shortlist_names_what_was_offered():
    got = hook.validate(proposal(observation_id="nope"), today=TODAY,
                        shortlists=shortlists())
    assert any("not in this lead's shortlist" in p for p in got), got
    assert any("abc123" in p for p in got), "it has to name what WAS offered"


def test_a_lead_with_no_shortlist_at_all_says_so_differently():
    """"the ranker offered something else" and "the ranker offered nothing" are
    different problems with different fixes."""
    got = hook.validate(proposal(observation_id="abc123"), today=TODAY,
                        shortlists={})
    assert any("has no shortlist" in p for p in got), got


# --------------------------------------------------------------- the escalation


def test_no_observation_id_and_no_escalation_is_a_hook_from_nowhere():
    """Before the flip a blank id was ordinary. Now it means one of two opposite
    things — the worker went and got something the shortlist did not have, or it
    composed a hook from nothing — and only the worker can say which."""
    got = hook.validate(proposal(observation_id=""), today=TODAY,
                        shortlists=shortlists())
    assert any("no provenance" in p for p in got), got


def test_a_declared_escalation_passes_and_is_named_in_the_report():
    escalated = proposal(observation_id="", escalated=True,
                         escalation_rung="podcast")
    assert hook.validate(escalated, today=TODAY, shortlists=shortlists()) == []
    text = hook.report([escalated], today=TODAY, shortlists=shortlists())
    assert "ESCALATED" in text and "podcast" in text


def test_an_escalation_with_no_rung_named_is_indistinguishable_from_a_guess():
    got = hook.validate(proposal(observation_id="", escalated=True),
                        today=TODAY, shortlists=shortlists())
    assert any("no rung named" in p for p in got), got


def test_escalating_and_joining_at_once_is_a_contradiction():
    """If the shortlist held it was not an escalation; if it did not, the
    observation_id belongs to something else."""
    got = hook.validate(proposal(observation_id="abc123", escalated=True,
                                 escalation_rung="podcast"),
                        today=TODAY, shortlists=shortlists())
    assert any("one or the other" in p for p in got), got


def test_the_report_says_when_the_join_was_not_checked():
    """A PASS with no shortlist passed a weaker check than a PASS with one, and
    the two lines have to be tellable apart."""
    text = hook.report([proposal()], today=TODAY)
    assert "NOT checked" in text


def test_a_hook_type_outside_the_crm_enum_is_caught_here():
    """Airtable rejects the value at the CRM write, which happens AFTER the
    email is in the upload file."""
    problems = hook.validate(proposal(hook_type="about_page"), today=TODAY)
    assert any("hook_type" in p for p in problems)


def test_the_report_refuses_to_read_as_verification():
    """A worker reading a PASS here as permission to skip the verifier has
    broken the only mechanism in this system that has ever caught a fabricated
    claim."""
    text = hook.report([proposal()], today=TODAY)
    assert "NOT VERIFICATION" in text
    assert "live re-fetch" in text


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
