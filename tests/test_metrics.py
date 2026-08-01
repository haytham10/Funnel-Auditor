"""What a batch yielded, and the one thing this module must never do.

Run: python -m pytest tests/test_metrics.py -q

The property these tests exist to protect: **a count nobody supplied prints `?`,
never `0`.** That is the dedupe wall's asymmetry and the ledger's, a third time.
A zero is a measurement; `?` is the honest word for a thing not measured, and a
metrics block that zero-fills is worse than no block because it looks like
evidence. Any change that makes an unsupplied number render as 0 is a regression
even if every other figure gets more accurate.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from outbound import ledger, metrics


def lead(state="verified", url="https://linkedin.com/posts/x-1",
         kind="WORK", key="a@x.ae", hook="something they did"):
    return {"lead_key": key, "email": key, "hook": hook, "hook_type": kind,
            "hook_verified": state, "hook_source_url": url}


def fetch(key="a@x.ae", by="apify:li_posts", cost=0.012, purpose="observe",
          url="https://linkedin.com/in/x"):
    return ledger.Retrieval(lead_key=key, stage="hook", platform="linkedin",
                            url=url, retrieved_by=by, cost_usd=cost,
                            secs=5.0, purpose=purpose)


# ------------------------------------------------------ the unsupplied count


def test_a_count_nobody_supplied_is_a_question_mark_not_a_zero():
    """The whole reason this module exists in this shape. An unsupplied raw
    count must never read as "no leads came in"."""
    out = metrics.from_research([lead()])
    for attr in ("raw", "after_dedupe", "warm", "passed_floors", "written",
                 "rejected", "tier0_rate", "source_list", "agent_passes"):
        assert getattr(out, attr) is metrics.UNKNOWN, attr
    block = metrics.batches_block(out)
    assert "Raw Count        ?" in block
    assert "NOT zero" in block


def test_an_unread_ledger_never_reports_a_cost_of_zero():
    """$0.0000 from an unopened ledger is the one wrong zero that would land in
    the CRM's currency field and be believed for months. A batch that spent
    nothing and a batch nobody costed are the same number and opposite facts."""
    out = metrics.from_research([lead()])
    assert out.ledger_read is False
    assert "Apify Cost USD   ?" in metrics.batches_block(out)
    assert "no ledger read" in metrics.report(out)


def test_a_read_ledger_that_really_spent_nothing_reports_zero():
    """The other half of the same distinction: a real zero is a finding and
    must print as one, or the `?` above means nothing."""
    out = metrics.from_research([lead()])
    metrics.add_ledger(out, [fetch(by="tier0", cost=0.0)], verified_leads={"a@x.ae"})
    assert out.ledger_read is True
    assert "Apify Cost USD   0.0000" in metrics.batches_block(out)


# --------------------------------------------------------- the hook outcomes


def test_the_four_outcomes_are_counted_apart():
    out = metrics.from_research([
        lead("verified", key="a@x.ae"),
        lead("verified", key="b@x.ae"),
        lead("refuted", key="c@x.ae"),
        lead("none", key="d@x.ae", hook=""),
        lead("proposed", key="e@x.ae"),
    ])
    assert (out.verified, out.refuted, out.none_found, out.proposed) == (2, 1, 1, 1)
    assert out.attempted == 5
    assert out.hook_yield == 0.4
    assert out.refute_rate == 0.2
    assert out.null_hook_rate == 0.2


def test_a_lead_that_never_reached_the_hook_stage_is_not_an_attempt():
    """A lead dropped at the floors did not produce a null hook — it produced no
    attempt. Folding them together would make null_hook_rate a function of how
    many leads failed the ICP, which is a different question."""
    out = metrics.from_research([lead("verified"), {"lead_key": "z@x.ae"}])
    assert out.leads == 2 and out.attempted == 1
    assert out.null_hook_rate == 0.0


def test_no_attempts_is_unknown_not_zero_percent():
    """Zero of zero hooks is not a 0% yield — it is a batch that never asked."""
    out = metrics.from_research([{"lead_key": "z@x.ae"}])
    assert out.hook_yield is None
    assert "hook_yield        ?" in metrics.report(out)


# ------------------------------------------------------------ yield_by_rung


def test_the_rung_is_derived_from_the_url_not_reported():
    """A worker naming its own rung can mislabel the number judging its rung.
    Same reason `select` derives the obs_id join rather than trusting a
    citation."""
    assert metrics.rung_of("https://linkedin.com/posts/x-1") == "li_posts"
    assert metrics.rung_of("https://open.spotify.com/episode/abc") == "podcast"
    assert metrics.rung_of("https://instagram.com/somecoach") == "ig_posts"
    assert metrics.rung_of("https://theircoaching.ae/about") == "about"
    assert metrics.rung_of("") == "none"


def test_yield_by_rung_counts_only_verified_hooks():
    """F5's number. A refuted hook from a rung is evidence against that rung,
    so counting it as yield would invert the finding."""
    out = metrics.from_research([
        lead("verified", url="https://linkedin.com/posts/a-1"),
        lead("verified", url="https://coach.ae/about", key="b@x.ae"),
        lead("refuted", url="https://coach.ae/about", key="c@x.ae"),
    ])
    assert out.yield_by_rung == {"li_posts": {"verified": 1},
                                 "about": {"verified": 1}}


# -------------------------------------------------------- wasted_retrieval


def test_wasted_retrieval_counts_paid_fetches_on_leads_that_produced_nothing():
    """The number this whole proposal set out to move."""
    out = metrics.from_research([lead("verified", key="a@x.ae"),
                                 lead("refuted", key="d@x.ae")])
    metrics.add_ledger(out, [
        fetch(key="a@x.ae", cost=0.012),
        fetch(key="d@x.ae", cost=0.012),
        fetch(key="d@x.ae", by="apify:ig_post", cost=0.021),
    ], verified_leads={"a@x.ae"})
    assert out.wasted_retrieval_n == 2
    assert out.wasted_retrieval_usd == 0.033


def test_free_rungs_are_not_wasted_spend():
    """Counting tier 0 and WebSearch would inflate a figure whose entire use is
    deciding whether a PURCHASE was worth making."""
    out = metrics.from_research([lead("refuted", key="d@x.ae")])
    metrics.add_ledger(out, [fetch(key="d@x.ae", by="tier0", cost=0.0),
                             fetch(key="d@x.ae", by="websearch", cost=0.0)],
                       verified_leads=set())
    assert out.wasted_retrieval_n == 0


def test_a_verification_fetch_is_never_wasted():
    """It is spent on a hook that exists, and it is the one duplicate this
    machine wants. R2 depends on it staying that way."""
    out = metrics.from_research([lead("refuted", key="d@x.ae")])
    metrics.add_ledger(out, [fetch(key="d@x.ae", cost=0.012, purpose="verify")],
                       verified_leads=set())
    assert out.wasted_retrieval_n == 0


def test_cost_per_verified_hook_is_unknown_when_none_verified():
    out = metrics.from_research([lead("refuted")])
    metrics.add_ledger(out, [fetch(cost=0.012)], verified_leads=set())
    assert out.cost_per_verified_hook is None
    assert "cost_per_hook     ?" in metrics.report(out)


# ------------------------------------------------------------- the reporting


def test_agent_passes_is_marked_as_reported_rather_than_measured():
    """Python cannot see an agent pass — the same blind spot that makes a
    worker's own WebSearch invisible to the ledger. `ledger add`'s answer is to
    record it and keep it distinguishable, and this does the same."""
    out = metrics.from_research([lead()])
    out.agent_passes = 14
    assert "14 — REPORTED, not measured" in metrics.report(out)


def test_the_report_says_it_never_fails_a_batch():
    """A gate that can halt a send file over an accounting line is a gate people
    learn to route around."""
    assert "OBSERVER" in metrics.report(metrics.from_research([lead()]))


def test_the_batches_block_mirrors_the_crm_field_names():
    """Airtable owns these names. A mirror that drifts sends somebody looking
    for a field that is not there."""
    labels = [label for label, _ in metrics.BATCH_FIELDS]
    assert labels[:4] == ["Batch", "Source List", "Raw Count", "After Dedupe"]
    assert "Tier 0 Rate" in labels and "Apify Cost USD" in labels


def test_the_artifact_round_trips(tmp_path):
    """A number that lived only in a terminal is the reason Part 2's cost claims
    had to be reconstructed from a hand-written journal entry."""
    import json

    out = metrics.from_research([lead()], batch="demo")
    written = metrics.write_artifact(out, tmp_path / "runs" / "demo-metrics.json")
    back = json.loads(written.read_text(encoding="utf-8"))
    assert back["batch"] == "demo" and back["verified"] == 1
    assert back["raw"] == metrics.UNKNOWN
