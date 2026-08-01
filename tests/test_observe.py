"""The observation contract: the evidence research used to throw away.

Run: python -m pytest tests/test_observe.py -q
 or: python tests/test_observe.py

The research object keeps a `_source` *string* per verdict — a URL or a page
name. So the LinkedIn post that settled `active_recent`, which is the exact
material a hook is made of, is read once, reduced to a boolean, discarded, and
paid for again one stage later. That is F1 and F2 of the retrieval proposal.

Nothing consumes observations yet and the duplicate fetch is deliberately still
made, so what these tests pin is the contract itself: that a record claiming to
be something fetched can be checked against reality at the moment it is written,
rather than found to be unusable by the stage that eventually needs it.

The check that matters most is `retrieved_by`. An observation naming a rung this
machine does not have is a record of a fetch that did not happen, and it would
look identical to a real one to every later reader.
"""

import os
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("OUTBOUND_LEDGER_ROOT",
                      tempfile.mkdtemp(prefix="outbound-ledger-"))

from outbound import observe, research


def obs(**overrides) -> observe.Observation:
    fields = {"lead_key": "a@b.com", "platform": "linkedin",
              "url": "https://linkedin.com/feed/update/1",
              "fetched_at": "2026-08-01T09:00:00", "published_at": "2026-07-20",
              "author": "self", "kind": "post",
              "text": "We ran the cohort with eleven founders this month.",
              "cost_usd": 0.02, "retrieved_by": "apify:li_posts"}
    fields.update(overrides)
    return observe.Observation(**fields)


TODAY = date(2026, 8, 1)


# ------------------------------------------------------------------ the enums


def test_a_real_observation_is_valid():
    assert observe.validate(obs(), today=TODAY) == []


def test_a_platform_outside_the_enum_is_caught():
    problems = observe.validate(obs(platform="linkdin"), today=TODAY)
    assert any("platform" in p for p in problems)


def test_a_kind_outside_the_enum_is_caught():
    problems = observe.validate(obs(kind="tweet"), today=TODAY)
    assert any("kind" in p for p in problems)


def test_an_author_outside_the_enum_is_caught():
    """`author` is ban #7 — no third-party coverage — waiting to stop being a
    sentence an agent is asked to remember. A third value would make the
    eventual `author == "self"` check quietly wrong rather than loud."""
    problems = observe.validate(obs(author="them"), today=TODAY)
    assert any("author" in p for p in problems)


# ---------------------------------------------------------------- the content


def test_a_post_with_no_text_was_reasoned_not_fetched():
    """The research contract's own rule, applied one layer down: a verdict that
    names nothing was reasoned. An observation that quotes nothing is the
    same claim."""
    problems = observe.validate(obs(text=""), today=TODAY)
    assert any("reasoned, not fetched" in p for p in problems)


def test_a_profile_fact_may_carry_no_text():
    """`bio` and `result` are facts about a profile, not a piece of content.
    Demanding a body from a follower count would make the honest record the
    invalid one."""
    assert observe.validate(obs(kind="bio", text=""), today=TODAY) == []


def test_an_observation_with_no_url_is_caught():
    problems = observe.validate(obs(url=""), today=TODAY)
    assert any("url" in p for p in problems)


# ------------------------------------------------------------------ the dates


def test_a_future_publication_date_is_caught():
    """A date nobody could have read is a date nobody fetched."""
    problems = observe.validate(obs(published_at="2026-09-01"), today=TODAY)
    assert any("future" in p for p in problems)


def test_a_malformed_publication_date_is_caught():
    problems = observe.validate(obs(published_at="July 2026"), today=TODAY)
    assert any("ISO date" in p for p in problems)


def test_no_publication_date_is_allowed():
    """An About page has no date and is still worth having. Demanding one
    would push a worker into inventing it, which is the failure this whole
    contract exists to make impossible."""
    assert observe.validate(obs(kind="about", published_at=""), today=TODAY) == []


def test_a_missing_fetch_time_is_caught():
    """Without it, staleness is unanswerable rather than merely unknown — an
    observation read at the start of a long batch is hours old by drafting."""
    problems = observe.validate(obs(fetched_at=""), today=TODAY)
    assert any("fetched_at" in p for p in problems)


def test_days_old_is_computed_from_the_publication_date():
    assert obs(published_at=(date.today() - timedelta(days=10)).isoformat()).days_old == 10
    assert obs(published_at="").days_old is None


# ------------------------------------------------------------- the retrieval


def test_an_apify_actor_this_machine_does_not_have_is_caught():
    """The check that matters most. A record naming a rung that does not exist
    is a record of a fetch that did not happen, and it reads exactly like a
    real one to everything downstream."""
    problems = observe.validate(obs(retrieved_by="apify:linkedin_scraper"),
                                today=TODAY)
    assert any("not an actor this machine has" in p for p in problems)


def test_every_real_actor_key_is_accepted():
    from audit.apify import ACTORS

    for key in ACTORS:
        assert observe.validate(obs(retrieved_by=f"apify:{key}"), today=TODAY) == []


def test_the_free_rungs_are_accepted():
    for source in observe.FREE_SOURCES:
        assert observe.validate(obs(retrieved_by=source, cost_usd=0.0),
                                today=TODAY) == []


def test_an_invented_retrieval_path_is_caught():
    problems = observe.validate(obs(retrieved_by="my own knowledge"), today=TODAY)
    assert any("retrieved_by" in p for p in problems)


def test_a_negative_cost_is_caught():
    problems = observe.validate(obs(cost_usd=-1.0), today=TODAY)
    assert any("cost_usd" in p for p in problems)


# ---------------------------------------------------------------------- ids


def test_the_same_observation_gets_the_same_id_twice():
    """Content-derived, so a post observed by two workers collapses to one id
    instead of two records that look independent."""
    a = observe.Observation.from_dict(obs().to_dict() | {"obs_id": ""})
    b = observe.Observation.from_dict(obs().to_dict() | {"obs_id": ""})
    assert a.obs_id and a.obs_id == b.obs_id


def test_the_same_page_for_two_leads_gets_two_ids():
    """A shared agency page is two observations, because the unit is
    (lead, source) and not source."""
    a = observe.Observation.from_dict(obs(lead_key="a@b.com").to_dict() | {"obs_id": ""})
    b = observe.Observation.from_dict(obs(lead_key="c@d.com").to_dict() | {"obs_id": ""})
    assert a.obs_id != b.obs_id


def test_an_id_a_worker_supplied_is_kept():
    kept = observe.Observation.from_dict(obs().to_dict() | {"obs_id": "deadbeef"})
    assert kept.obs_id == "deadbeef"


def test_a_null_field_becomes_its_default_not_a_crash():
    """`"published_at": null` is the honest JSON for "it carries no date". It
    must not arrive as a TypeError inside the gate, which reads like a crashed
    check rather than a clean record."""
    loaded = observe.Observation.from_dict({"url": "https://x/1",
                                            "published_at": None,
                                            "text": None})
    assert loaded.published_at == "" and loaded.text == ""


def test_an_unknown_key_is_dropped():
    loaded = observe.Observation.from_dict({"url": "https://x/1", "rung": 4})
    assert loaded.url == "https://x/1"


# ------------------------------------------------------- inside the research


def test_a_research_object_with_no_observations_is_still_valid():
    """Additive means additive. Every existing worker output must keep passing
    unchanged."""
    obj = research.Research(slug="x", name="X")
    assert research.validate(obj) == []


def test_a_malformed_observation_makes_the_research_object_invalid():
    obj = research.Research(slug="x", name="X",
                            observations=[obs(platform="linkdin").to_dict()])
    problems = research.validate(obj)
    assert any("observation[0]" in p and "platform" in p for p in problems)


def test_a_good_observation_does_not_make_the_research_object_invalid():
    obj = research.Research(slug="x", name="X", observations=[obs().to_dict()])
    assert research.validate(obj) == []


def test_one_bad_slice_cannot_bury_the_floor_violations():
    """A report that flags forty identical lines is a report nobody reads, and
    the floor verdict underneath them is the thing that drops a row."""
    obj = research.Research(slug="x", name="X", uae_based="no",
                            observations=[obs(platform="x").to_dict()] * 40)
    problems = research.validate(obj)
    assert any("uae_based=no with no source" in p for p in problems)
    assert any("more observation problem(s)" in p for p in problems)
    assert len(problems) <= research.MAX_OBSERVATION_PROBLEMS + 3


def test_the_worker_instructions_carry_the_observation_shape():
    """`schema_help` is generated from the dataclass rather than written down,
    so a field added here reaches research-worker without anyone editing prose.
    That only holds while the nested shape is actually appended."""
    text = research.schema_help()
    assert "observations" in text
    assert "VERBATIM" in text


# ------------------------------------------------------------------- loading


def test_one_observation_or_a_list_both_load():
    assert len(observe.load(obs().to_dict())) == 1
    assert len(observe.load([obs().to_dict(), obs().to_dict()])) == 2


def test_validate_all_says_which_observation_was_wrong():
    problems = observe.validate_all(
        [obs(), obs(platform="x")], today=TODAY)
    assert problems and problems[0].startswith("observation[1]")


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
