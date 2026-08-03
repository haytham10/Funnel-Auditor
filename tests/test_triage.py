"""The pre-spend sort, and the one asymmetry it is allowed to have.

Run: python -m pytest tests/test_triage.py -q
 or: python tests/test_triage.py

Triage exists to stop a 237-row scrape from being researched at four agent
passes a lead. That makes it the most dangerous stage in the machine to get
wrong, because everything it does is invisible: a lead it drops is never
researched, never drafted, and never appears in a report anybody reads.

So the tests that matter here are the ones about NOT dropping. `unclear` is
HOLD. A missing "Dubai" is HOLD. A missing coach word is HOLD. The only `no`
this stage can reach on its own evidence is a stale activity date, and only when
the caller asserts the corpus is complete — which is true of a profile scrape
and false of a research pass, and the default is false.
"""

import os
import sys
import tempfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("OUTBOUND_LEDGER_ROOT",
                      tempfile.mkdtemp(prefix="outbound-ledger-"))
os.environ.setdefault("OUTBOUND_COPY_SOURCE", "csv")

from outbound import observe, triage                          # noqa: E402
from outbound.normalize import Lead                           # noqa: E402

TODAY = date(2026, 8, 3)


def _lead(**over) -> Lead:
    lead = Lead(name="Rita Baki", slug="rita-baki",
                headline="Neuro Coach", instagram_url="https://instagram.com/x")
    for key, value in over.items():
        setattr(lead, key, value)
    return lead


def _obs(published: str, text: str = "Dubai coaches, here is what I learned",
         **over) -> observe.Observation:
    obs = observe.Observation(
        lead_key="k", platform="instagram", url="https://instagram.com/p/1/",
        fetched_at="2026-08-02T12:00:00Z", published_at=published,
        author="self", kind="post", text=text, retrieved_by="apify:ig_profile")
    for key, value in over.items():
        setattr(obs, key, value)
    return obs


def test_all_three_floors_yes_is_a_run():
    result = triage.triage_lead(_lead(city="Dubai"), [_obs("2026-08-01")],
                                complete_corpus=True, today=TODAY)
    assert result.tier == triage.RUN


def test_no_location_anywhere_is_hold_and_never_drop():
    """The one that matters. A coach who does not write "Dubai" in their bio is
    a coach we do not have a location for — absence of evidence, and a false
    kill is permanent and invisible."""
    result = triage.triage_lead(_lead(), [_obs("2026-08-01", text="Monday reset")],
                                complete_corpus=True, today=TODAY)
    assert result.uae == "unclear"
    assert result.tier == triage.HOLD


def test_no_coach_word_anywhere_is_hold_and_never_drop():
    result = triage.triage_lead(
        _lead(headline="Founder"), [_obs("2026-08-01", text="Dubai sunrise")],
        complete_corpus=True, today=TODAY)
    assert result.tier == triage.HOLD


def test_a_lead_with_no_observations_at_all_is_hold():
    """A private or quiet account is nothing to judge. Absence of the corpus is
    not a measurement of the lead."""
    result = triage.triage_lead(_lead(city="Dubai"), [],
                                complete_corpus=True, today=TODAY)
    assert result.active == "unclear"
    assert result.tier == triage.HOLD


# ------------------------------------------------- the one allowed asymmetry


def test_a_complete_corpus_of_stale_posts_drops_the_lead():
    """`latestPosts` is what the account HAS, read off the platform on the
    dump's date. "The newest of twelve is eight months old" is a measurement of
    the lead, not of our retrieval."""
    result = triage.triage_lead(_lead(city="Dubai"), [_obs("2025-12-01")],
                                complete_corpus=True, today=TODAY)
    assert result.active == "no"
    assert result.tier == triage.DROP
    assert "stale" in result.reason


def test_the_same_stale_posts_without_the_assertion_are_only_unclear():
    """A research worker's observations are a sample of what it happened to
    fetch. `activity_from_observations` moves the floor upward only, and this
    module does not get to loosen that for everybody."""
    result = triage.triage_lead(_lead(city="Dubai"), [_obs("2025-12-01")],
                                complete_corpus=False, today=TODAY)
    assert result.active == "unclear"
    assert result.tier == triage.HOLD


def test_a_third_party_post_cannot_keep_a_lead_alive_or_kill_one():
    """Somebody else's post about them is not evidence they did anything —
    the same rule `activity_from_observations` and `select` both apply."""
    fresh_but_theirs = _obs("2026-08-01", author="third_party")
    result = triage.triage_lead(_lead(city="Dubai"), [fresh_but_theirs],
                                complete_corpus=True, today=TODAY)
    assert result.active == "unclear"
    assert result.tier == triage.HOLD


def test_a_stated_non_coach_occupation_is_the_other_drop():
    result = triage.triage_lead(
        _lead(headline="Cabin crew"),
        [_obs("2026-08-01", text="Dubai layover")],
        complete_corpus=True, today=TODAY)
    assert result.tier == triage.DROP
    assert "not a coach" in result.reason


def test_every_verdict_carries_the_source_that_settled_it():
    """A drop with no source is a guess wearing a verdict's clothes, and the
    DROP list is meant to be arguable."""
    result = triage.triage_lead(_lead(city="Dubai"), [_obs("2025-12-01")],
                                complete_corpus=True, today=TODAY)
    assert result.active_source
    assert result.uae_source


def test_triage_all_joins_observations_on_the_lead_key():
    from outbound.fetch import lead_key

    lead = _lead(city="Dubai")
    obs = _obs("2026-08-01")
    obs.lead_key = lead_key(lead)
    results = triage.triage_all([lead], [obs], complete_corpus=True, today=TODAY)
    assert results[0].tier == triage.RUN
    assert results[0].observations == 1


def test_the_report_prints_every_drop_rather_than_a_count():
    """A drop is the only irreversible thing here and the operator reading them
    is the gate. A summarised DROP list is a gate nobody can use."""
    stale = [triage.triage_lead(_lead(name=f"Coach {i}", city="Dubai"),
                                [_obs("2025-12-01")],
                                complete_corpus=True, today=TODAY)
             for i in range(3)]
    text = triage.report(stale)
    assert text.count("stale") >= 3
    for i in range(3):
        assert f"Coach {i}" in text


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {name}")
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"FAIL {name}: {type(exc).__name__}: {exc}")
    sys.exit(1 if failures else 0)
