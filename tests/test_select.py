"""Choosing a hook's evidence without fetching, and measuring whether it agrees.

Run: python -m pytest tests/test_select.py -q
 or: python tests/test_select.py

The hook stage is the last consequential stage that searches, and the reason
nobody can say whether it needs to is that the question has never been asked
mechanically. These tests pin the ranker and, more importantly, the comparison —
because the comparison is what the next batch is being run to produce.

**The comparison has five verdicts and the split that matters is `missed`
against `unobserved`.** One says the ranker had the page and passed it over,
which is fixable in three lines; the other says the page was never fetched by
the research stage at all, which is the fetch that cannot be removed. Collapsing
them yields a percentage nobody can act on. A test here holds them apart because
the first cut of `compare` got it wrong: a candidate that survived every ban and
merely ranked fourth was reported as `unobserved`, which is the same word for
"we never saw it" and inflates the number that decides the flip.

**And nothing here verifies anything.** A quote found in the text we stored is
in *our copy*, not on the page. The verifier's live re-fetch is the only thing
that has ever caught a fabricated claim, and the day this module's output reads
as verification, R2 has happened.
"""

import os
import sys
import tempfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("OUTBOUND_LEDGER_ROOT",
                      tempfile.mkdtemp(prefix="outbound-ledger-"))

from outbound import lint, observe, select

TODAY = date(2026, 8, 1)


def obs(**overrides) -> observe.Observation:
    fields = {"lead_key": "nadia@nadiacoaching.ae", "platform": "linkedin",
              "url": "https://linkedin.com/posts/nadia-1",
              "fetched_at": "2026-08-01T09:00:00", "published_at": "2026-07-20",
              "author": "self", "kind": "post",
              "text": "We ran the cohort with eleven founders this month and "
                      "the retention surprised me more than the signups did.",
              "cost_usd": 0.02, "retrieved_by": "apify:li_posts"}
    fields.update(overrides)
    return observe.Observation.from_dict(fields)


def research(*observations, **overrides) -> dict:
    row = {"name": "Nadia Karim", "email": "nadia@nadiacoaching.ae",
           "observations": [o.to_dict() for o in observations]}
    row.update(overrides)
    return row


# ------------------------------------------------------------------- the bans


def test_a_real_observation_survives_every_ban():
    assert select.ban_for(obs(), today=TODAY) == ""


def test_third_party_coverage_is_excluded():
    """Ban #7. A directory listing or an article about them is not their voice,
    and it is `author == "third_party"` rather than a sentence to remember."""
    assert select.ban_for(obs(author="third_party"), today=TODAY) == "third_party"


def test_unknown_authorship_is_not_excluded():
    """`AUTHORS` is three-valued and `unknown` is the default. `resolve`'s rule
    holds one stage over: unknown never means the tell said no. Filtering on
    `self` would reject most of a real pool for a field nobody had to fill, and
    authorship is still the live verifier's call."""
    assert select.ban_for(obs(author="unknown"), today=TODAY) == ""


def test_self_outranks_unknown():
    theirs, maybe = obs(author="self"), obs(author="unknown", url="https://x.ae/2")
    assert select.sort_key(theirs, today=TODAY) < select.sort_key(maybe, today=TODAY)


def test_an_about_page_is_offered_and_ranked_last():
    """F5's narrowing, reversed on batch evidence. All three MISSED leads in
    `2026-08-01-q1` were `kind: about` observations an independent verifier had
    VERIFIED, and one ban accounted for 21 of the corpus's 32 rejections.

    What the verifier refuses is the generic, not the location. So an About page
    is offered — and `KIND_RANK` keeps it behind anything else the lead has,
    which is the job the ban was doing badly."""
    about = obs(platform="site", kind="about", published_at="")
    assert select.ban_for(about, today=TODAY) == ""
    assert select.sort_key(about, today=TODAY) > select.sort_key(obs(), today=TODAY)


def test_an_about_page_carries_the_evergreen_date_exemption():
    """Removing the location ban alone changes nothing: a page somebody wrote
    about themselves has no publication date, so those same three leads would
    have moved from `site_prose` to `no_date`. `docs/hook-rules.md` grants both
    halves and the code carried only one.

    Briefly reversed on 2026-08-02 and restored the same day. The batch that
    prompted it exposed a real defect, but the defect was `outbound/hook.py`
    demanding a date from every proposal — which left a worker handed a
    legitimate undated page choosing between abandoning the hook and inventing
    the date. Deleting the fallback removes the symptom and the fallback. The
    gate was fixed instead; this exemption stays."""
    assert "about" in select.EVERGREEN_KINDS
    assert select.ban_for(obs(platform="site", kind="about", published_at=""),
                          today=TODAY) == ""
    assert select.ban_for(obs(platform="site", kind="about",
                              published_at="2019-03-01"), today=TODAY) == ""


def test_an_about_page_is_the_fallback_and_never_the_preference():
    """What makes offering it safe: it is ranked below everything datable, so a
    lead only ever sees one when nothing recent survived."""
    fresh = obs(published_at="2026-07-28")
    about = obs(platform="site", kind="about", published_at="",
                url="https://nadiacoaching.ae/about")
    ranked, _ = select.rank([about, fresh], today=TODAY)
    assert [c.kind for c in ranked] == ["post", "about"]


def test_a_post_on_their_own_site_is_content():
    """The other half of the location ban: a blog post somebody published on
    their own domain was excluded for being on a site, which is a statement
    about the host and not about the writing."""
    text = "The Four Doors model is how I sequence a founder's first ninety days."
    assert select.ban_for(obs(platform="site", kind="framework", text=text,
                              published_at="2026-07-28"), today=TODAY) == ""
    assert select.ban_for(obs(platform="site", kind="post"), today=TODAY) == ""


def test_the_same_text_on_two_leads_pages_is_generic_by_evidence():
    """Ban #1's mechanical half, and the only proxy for "generic" that is not a
    guess: the verifier's own test is whether it could be sent unedited to
    another coach in the segment, and two leads carrying it is that, proven."""
    shared = "Book a free discovery call and let us start your journey today."
    mine = obs(lead_key="a@x.ae", platform="site", kind="about", text=shared)
    theirs = obs(lead_key="b@y.ae", platform="site", kind="about", text=shared)
    boilerplate = select.boilerplate_of([(o.lead_key, o.text)
                                         for o in (mine, theirs)])
    assert select.ban_for(mine, today=TODAY, boilerplate=boilerplate) \
        == "boilerplate"
    # And judged alone, with no corpus to compare against, it is not generic —
    # the test needs evidence and says so rather than guessing from one record.
    assert select.ban_for(mine, today=TODAY) == ""


def test_one_leads_page_fetched_twice_is_not_boilerplate():
    """A duplicate fetch is the ledger's business. Convicting a lead's only
    observation of being generic because we retrieved it twice would turn an
    accounting problem into a lost lead."""
    text = "I closed the studio's books myself before I ever coached the owner."
    twice = [("a@x.ae", text), ("a@x.ae", text)]
    assert select.boilerplate_of(twice) == frozenset()


def test_two_anonymous_observations_do_not_convict_each_other():
    """A blank lead key stands only for itself. Grouping every keyless
    observation under "" would make one lead's page generic on the strength of
    another record nobody could attribute."""
    text = "I closed the studio's books myself before I ever coached the owner."
    assert select.boilerplate_of([("", text), ("", text)]) == frozenset()


def test_a_link_in_bio_button_wall_is_never_offered():
    """`resolve` writes a `bio` observation for every linktree it reads. Without
    this every link-in-bio lead's top pick is its own list of buttons."""
    assert select.ban_for(obs(platform="linkinbio", kind="bio"), today=TODAY) \
        == "not_content"


def test_stale_news_is_not_fresh():
    """Ban #6, as a date comparison."""
    assert select.ban_for(obs(published_at="2025-01-05"), today=TODAY) == "stale"


def test_a_post_with_no_date_cannot_prove_it_is_recent():
    assert select.ban_for(obs(published_at=""), today=TODAY) == "no_date"


def test_an_evergreen_framework_is_exempt_from_both_date_rules():
    """`docs/hook-rules.md` grants it: an evergreen framework or a line they
    wrote themselves is fine at any age."""
    text = "The Four Doors model is how I sequence a founder's first ninety days."
    assert select.ban_for(obs(platform="youtube", kind="framework", text=text,
                              published_at=""), today=TODAY) == ""
    assert select.ban_for(obs(platform="youtube", kind="framework", text=text,
                              published_at="2019-03-01"), today=TODAY) == ""


def test_the_recency_window_is_the_hook_window_not_the_activity_floor():
    """Two windows, two owners. There were once four, which is three too many
    for one stage: the activity floor is 30 days and belongs to `qualify`."""
    from outbound import qualify

    assert select.HOOK_RECENCY_DAYS == 90
    assert qualify.ACTIVITY_WINDOW_DAYS == 30
    assert select.HOOK_RECENCY_DAYS != qualify.ACTIVITY_WINDOW_DAYS


def test_something_too_short_to_quote_is_not_offered():
    assert select.ban_for(obs(text="Great week."), today=TODAY) == "too_short"


def test_the_short_floor_is_the_linter_s_and_not_a_second_number():
    """Measured against `lint.MIN_HOOK_WORDS` itself, so moving that number
    moves this rule rather than leaving a second copy behind."""
    exactly = " ".join(["word"] * lint.MIN_HOOK_WORDS)
    one_short = " ".join(["word"] * (lint.MIN_HOOK_WORDS - 1))
    assert select.ban_for(obs(text=exactly), today=TODAY) == ""
    assert select.ban_for(obs(text=one_short), today=TODAY) == "too_short"


# --------------------------------------------------------------- the ranking


def test_the_batch_artifacts_keep_the_corpus_and_not_only_the_verdict():
    """`2026-08-01-q1` committed its selections and left the research objects in
    `work/`, which does not survive the container. So when the ban behind all
    three MISSED turned out to be wrong, the batch that proved it could not be
    re-scored: the selections carry a shortlist, and a rejection carries a ban
    name and a URL, neither of which can be ranked again.

    The corpus is the input, byte for byte, so `select <corpus> --against`
    answers any later change to the bans without paying for a run."""
    import json
    import subprocess

    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, OUTBOUND_LEDGER_ROOT=tmp)
        rows = [research(obs(), name="Nadia Karim",
                         hook_verified="verified",
                         hook_source_url="https://linkedin.com/posts/nadia-1")]
        source = Path(tmp) / "draftable.json"
        source.write_text(json.dumps(rows), encoding="utf-8")

        proc = subprocess.run(
            [sys.executable, "main.py", "select", str(source), "--against",
             "--batch", "test-batch"],
            cwd=Path(__file__).resolve().parent.parent,
            capture_output=True, text=True, env=env)
        assert proc.returncode == 0, proc.stdout + proc.stderr

        runs = Path(tmp) / "data" / "runs"
        assert json.loads((runs / "test-batch-research.json").read_text()) == rows
        assert "selections" in json.loads(
            (runs / "test-batch-select.json").read_text())


def test_the_run_artifacts_all_honour_one_root():
    """Three commands write into `data/runs/` and each had built the path from
    its own string literal, so none of them could be redirected and a test of
    any one wrote beside real batches."""
    from outbound import ledger

    with tempfile.TemporaryDirectory() as tmp:
        for suffix in ("-select.json", "-metrics.json", "-replies.json"):
            got = ledger.artifact(suffix, batch="b", root=tmp)
            assert got == Path(tmp) / ledger.RUNS_DIR / f"b{suffix}"
        assert ledger.path(batch="b", root=tmp).name == "b.jsonl"


def test_the_ranking_is_enum_positions_and_not_a_score():
    """`resolve` states the rule: nothing in this repo carries a numeric
    confidence, and one batch of 151 leads cannot calibrate a scale."""
    assert not hasattr(select.Candidate(), "score")
    key = select.sort_key(obs(), today=TODAY)
    assert all(isinstance(part, (int, str)) for part in key)


def test_every_kind_has_a_rank():
    """A kind missing from the map sorts to the same bucket as an about page,
    silently. `KINDS` grew twice already."""
    for kind in observe.KINDS:
        assert kind in select.KIND_RANK


def test_the_platform_order_is_observe_s_and_not_a_second_copy():
    assert list(select.PLATFORM_RANK) == list(observe.PLATFORMS)


def test_a_recent_post_outranks_an_older_one():
    fresh = obs(published_at="2026-07-28")
    older = obs(published_at="2026-06-01", url="https://linkedin.com/posts/n-2")
    ranked, _ = select.rank([older, fresh], today=TODAY)
    assert ranked[0].published_at == "2026-07-28"


def test_an_undated_framework_sorts_last_rather_than_crashing():
    """`days_old` is None for both 'no date' and 'unparseable date', and a None
    in a sort key raises TypeError on the first evergreen framework."""
    text = "The Four Doors model is how I sequence a founder's first ninety days."
    evergreen = obs(platform="site", kind="framework", text=text, published_at="",
                    url="https://nadiacoaching.ae/method")
    ranked, _ = select.rank([evergreen, obs()], today=TODAY)
    assert ranked[0].kind == "post"
    assert [c.kind for c in ranked][-1] == "framework"


def test_the_shortlist_is_three():
    pool = [obs(url=f"https://linkedin.com/posts/n-{i}",
                published_at=f"2026-07-{10 + i:02d}") for i in range(6)]
    ranked, _ = select.rank(pool, today=TODAY)
    assert len(ranked) == select.SHORTLIST == 3
    assert [c.rank for c in ranked] == [1, 2, 3]


def test_a_rejection_names_the_ban_that_fired():
    """A wrong rule is a three-line fix; a low agreement number with no reasons
    is nothing anybody can act on."""
    _, rejected = select.rank([obs(author="third_party")], today=TODAY)
    assert rejected[0]["ban"] == "third_party"


def test_the_quote_is_the_observation_text_verbatim():
    """A summarised quote reads fine, ranks fine, and produces a hook whose
    words are not on the page — the failure the verifier exists to catch,
    arriving through the one door it does not watch."""
    source = obs()
    ranked, _ = select.rank([source], today=TODAY)
    assert ranked[0].quote == source.text


def test_two_runs_over_the_same_pool_are_identical():
    pool = [obs(url=f"https://linkedin.com/posts/n-{i}") for i in range(4)]
    first, _ = select.rank(pool, today=TODAY)
    second, _ = select.rank(list(reversed(pool)), today=TODAY)
    assert [c.to_dict() for c in first] == [c.to_dict() for c in second]


# ----------------------------------------------------------- the measurement


def test_agreed_when_the_top_pick_is_the_page_the_hook_cited():
    result = select.select_all(
        [research(obs(), hook_verified="verified",
                  hook_source_url="https://linkedin.com/posts/nadia-1")],
        against=True, today=TODAY)
    assert result["selections"][0].agreement == "agreed"


def test_shortlisted_when_the_hook_s_page_is_not_the_top_pick():
    fresh = obs(published_at="2026-07-30", url="https://linkedin.com/posts/n-new")
    result = select.select_all(
        [research(fresh, obs(), hook_verified="verified",
                  hook_source_url="https://linkedin.com/posts/nadia-1")],
        against=True, today=TODAY)
    assert result["selections"][0].agreement == "shortlisted"


def test_missed_when_a_ban_excluded_the_page_the_hook_used():
    result = select.select_all(
        [research(obs(published_at="2025-01-05"), hook_verified="verified",
                  hook_source_url="https://linkedin.com/posts/nadia-1")],
        against=True, today=TODAY)
    selection = result["selections"][0]
    assert selection.agreement == "missed"
    assert "stale" in selection.agreement_note


def test_missed_when_the_page_survived_every_ban_but_ranked_out():
    """The bug this test exists for: a candidate that passed every ban and
    merely ranked fourth was reported as `unobserved`, which is the same word
    used for a page nothing ever fetched. Those say opposite things about
    whether the hook stage's fetch can be removed."""
    pool = [obs(url=f"https://linkedin.com/posts/n-{i}",
                published_at=f"2026-07-{20 + i:02d}") for i in range(5)]
    result = select.select_all(
        [research(*pool, hook_verified="verified",
                  hook_source_url="https://linkedin.com/posts/n-0")],
        against=True, today=TODAY)
    selection = result["selections"][0]
    assert selection.agreement == "missed"
    assert "below the shortlist" in selection.agreement_note


def test_unobserved_when_the_hook_cited_a_page_nothing_retrieved():
    """The number that decides the flip: precisely the fetch selection could
    not have replaced."""
    result = select.select_all(
        [research(obs(), hook_verified="verified",
                  hook_source_url="https://linkedin.com/posts/never-seen")],
        against=True, today=TODAY)
    assert result["selections"][0].agreement == "unobserved"


def test_no_pool_is_not_the_ranker_s_failure():
    """A lead whose research worker returned no observations measures the
    corpus, not the ranker. Charging the ranker for somebody else's empty
    return produces a number nobody can act on."""
    result = select.select_all(
        [research(hook_verified="verified",
                  hook_source_url="https://linkedin.com/posts/x")],
        against=True, today=TODAY)
    assert result["selections"][0].agreement == "no_pool"


def test_a_lead_with_no_verified_hook_is_not_compared():
    result = select.select_all(
        [research(obs(), hook_verified="proposed",
                  hook_source_url="https://linkedin.com/posts/nadia-1")],
        against=True, today=TODAY)
    assert result["selections"][0].agreement == ""


def test_a_trailing_slash_does_not_manufacture_a_disagreement():
    result = select.select_all(
        [research(obs(), hook_verified="verified",
                  hook_source_url="https://linkedin.com/posts/nadia-1/")],
        against=True, today=TODAY)
    assert result["selections"][0].agreement == "agreed"


# ------------------------------------------------------------------ the gate


def test_every_lead_gets_a_selection_including_one_with_nothing():
    result = select.select_all([research(), research(obs())], today=TODAY)
    assert len(result["selections"]) == 2
    assert result["selections"][0].pick is None


def test_no_candidate_is_a_good_answer_and_not_a_failure():
    """No hook found is a good answer: the lead holds and gets no row."""
    result = select.select_all([research(obs(author="third_party"))], today=TODAY)
    assert select.validate_all(result["selections"]) == []


def test_a_selection_with_no_lead_key_is_caught():
    problems = select.validate(select.LeadSelection())
    assert any("lead_key" in p for p in problems)


def test_a_candidate_with_no_obs_id_is_caught():
    """The join is what proves a hook came from something retrieved rather than
    something composed — ban #3, made mechanical."""
    selection = select.LeadSelection(lead_key="a@b.ae", shortlist=[
        select.Candidate(obs_id="", platform="linkedin", url="https://x.ae",
                         kind="post", quote="words here", rank=1)])
    assert any("obs_id" in p for p in select.validate(selection))


def test_broken_ranks_are_caught():
    """A reader cannot tell which one would have been used."""
    selection = select.LeadSelection(lead_key="a@b.ae", shortlist=[
        select.Candidate(obs_id="a", platform="linkedin", url="https://x.ae",
                         kind="post", quote="w", rank=1),
        select.Candidate(obs_id="b", platform="linkedin", url="https://y.ae",
                         kind="post", quote="w", rank=5)])
    assert any("1..2" in p for p in select.validate(selection))


def test_an_agreement_outside_the_enum_is_caught():
    selection = select.LeadSelection(lead_key="a@b.ae", agreement="probably")
    assert any("agreement" in p for p in select.validate(selection))


def test_a_selection_survives_json_and_back():
    result = select.select_all([research(obs())], today=TODAY)
    built = result["selections"][0]
    restored = select.load({"selections": [built.to_dict()]})[0]
    assert restored.to_dict() == built.to_dict()


# ------------------------------------------------------------------ the report


def test_the_report_never_claims_a_quote_is_verified():
    """R2 in one assertion. The moment this output reads as verification, the
    verifier's live fetch starts looking like overhead.

    Asserted on the property rather than a sentence: the report has to say the
    text is *stored*, and it has to name the live re-fetch as the thing that
    checks the page. Post-flip this is the more important of the two — the quote
    now comes from text a different agent wrote down hours earlier."""
    report = select.select_all([research(obs())], today=TODAY)["report"]
    lowered = report.lower()
    assert "stored" in lowered
    assert "re-fetch" in lowered or "live" in lowered
    assert "verified on the page" not in lowered.replace("are on the page", "")


def test_the_report_names_the_missed_pages_rather_than_only_counting_them():
    result = select.select_all(
        [research(obs(published_at="2025-01-05"), hook_verified="verified",
                  hook_source_url="https://linkedin.com/posts/nadia-1")],
        against=True, today=TODAY)
    assert "MISSED" in result["report"]


def test_unobserved_reads_as_the_escalation_rate_after_the_flip():
    """The same word, the opposite meaning. Before the flip an `unobserved` hook
    was a fetch selection could not have replaced — the number that decided
    whether the flip could go at all. After it, the hook comes from the
    shortlist, so a hook citing a page no observation carries is one the worker
    escalated to get.

    The verdict needs no code change to say that; the report has to."""
    result = select.select_all(
        [research(obs(), hook_verified="verified",
                  hook_source_url="https://podcast.fm/ep/12")],
        against=True, today=TODAY)
    assert "1 of 1 escalated" in result["report"]
    assert "escalation rate" in result["report"]


def test_the_report_asks_for_the_hook_room_rather_than_assuming_it():
    """`deal` prints the room before this stage now, but it is handed in and
    never derived here. MIN_HOOK_WORDS is a FLOOR on the hook, and reusing it
    as a ceiling would be one number wearing two meanings in two stages."""
    result = select.select_all([research(obs())], today=TODAY)
    assert "hook room not given" in result["report"]
    assert "--hook-room" in result["report"]


def test_the_room_is_reported_when_it_is_given():
    result = select.select_all([research(obs())], hook_room=24, today=TODAY)
    assert "hook room 24 words, advisory only" in result["report"]


# --------------------------------------------------------- the standalone path

if __name__ == "__main__":
    import inspect

    failures = 0
    for name, fn in sorted(globals().items()):
        if not (name.startswith("test_") and callable(fn)):
            continue
        if inspect.signature(fn).parameters:
            print(f"SKIP {name} (needs a pytest fixture)")
            continue
        try:
            fn()
            print(f"ok   {name}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"FAIL {name}: {type(exc).__name__}: {exc}")
    sys.exit(1 if failures else 0)
