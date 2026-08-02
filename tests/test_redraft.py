"""The drafting loop, decided in code instead of one lead at a time.

Run: python -m pytest tests/test_redraft.py -q
 or: python tests/test_redraft.py

Two measured failures produced this module, and each test pins one of them.

**The cap was a sentence and the sentence lost.** `SKILL.md` has always said a
REWRITE goes back to the drafter once and then the lead holds. On
`2026-08-02-q2` eight of nine leads exceeded it, one running five rounds; on
`2026-08-02-q3` eight leads exceeded it and three ran three rounds. The repeats
were 68% and 46% of those draft stages. A long session talks itself past a
sentence one reasonable exception at a time; it cannot talk itself past a loop
bound.

**Seventeen identical findings were answered seventeen times.** Every q3 draft
failed its first cold read on the same beat. The redraft prompts ran 1.6x the
size of all seventeen original briefs together. Nobody was careless — a reader
going lead by lead cannot see the seventeenth until they have paid for sixteen.
Counting is what makes a repetition visible on the first pass, and counting is
why `beat` is an enum rather than free text.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from outbound import redraft, verdict


def cold(slug, verd="REWRITE", *, round=1, beats=("identity",),
         problem="the identity beat is the copy line with a `your` bolted on"):
    return verdict.Verdict.from_dict({
        "slug": slug, "verdict": verd, "round": round,
        "seam": "no", "voice": "flat",
        "problems": [{"beat": b, "sentence": "a sentence", "problem": problem}
                     for b in beats] if verd == "REWRITE" else []})


def test_a_lead_at_the_cap_holds_instead_of_going_back_a_third_time():
    """q2 ran one lead five rounds and q3 ran three leads three. The cap was
    always specified; it was never enforceable."""
    out = redraft.plan([cold("a", round=1), cold("b", round=2)])
    assert out.redraft == ["a"]
    assert out.hold == ["b"]
    assert "cap is 2" in out.reasons["b"]


def test_seventeen_drafts_failing_on_one_beat_produce_one_note():
    """The exact shape of 2026-08-02-q3. Seventeen individual rewrite notes
    were written before the repetition was treated as the signal."""
    wave = [cold(f"lead{n}") for n in range(17)]
    out = redraft.plan(wave)
    assert len(out.shared) == 1
    entry = out.shared[0]
    assert entry["beat"] == "identity"
    assert entry["n"] == 17 and entry["share"] == 1.0
    text = redraft.report(out)
    assert "fix the stage, not the leads" in text
    # The seventeen per-lead lines are not reprinted under the shared block.
    assert text.count("redraft lead") == 0
    assert "17 more redrafted lead(s) are named in the SHARED" in text


def test_genuinely_separate_problems_do_not_get_a_shared_note():
    """Clustering a wave of one-off findings would be worse than not clustering
    — it would tell the drafter a stage is broken when one email is."""
    out = redraft.plan([cold("a", beats=("identity",)),
                        cold("b", beats=("cta",)),
                        cold("c", beats=("ps",))])
    assert out.shared == []
    assert "no beat reaches 2 leads" in redraft.report(out)


def test_a_send_ships_and_a_reject_holds_without_a_second_pass():
    out = redraft.plan([cold("a", "SEND"), cold("b", "REJECT"), cold("c")])
    assert out.ship == ["a"] and out.hold == ["b"] and out.redraft == ["c"]
    assert "no row" in out.reasons["b"]


def test_a_rewrite_naming_nothing_is_a_schema_failure():
    """It would send a drafter back with no instruction: a full opus pass that
    cannot improve on anything, which is the most expensive possible outcome."""
    bad = verdict.Verdict.from_dict({"slug": "a", "verdict": "REWRITE"})
    problems = verdict.validate(bad)
    assert any("no instruction" in p for p in problems)


def test_a_beat_outside_the_enum_is_rejected_so_clustering_stays_possible():
    """"the identity line" and "identity beat" would be two buckets, and the
    pattern the clustering exists to find would disappear again."""
    bad = verdict.Verdict.from_dict({
        "slug": "a", "verdict": "REWRITE",
        "problems": [{"beat": "the identity line", "sentence": "x",
                      "problem": "y"}]})
    assert any("is not one of" in p for p in verdict.validate(bad))


def test_a_verdict_outside_the_enum_is_not_routable():
    out = redraft.plan([cold("a", "MAYBE")])
    assert out.hold == ["a"]
    assert "not routable" in out.reasons["a"]


def test_routing_never_fails_the_batch():
    """A wave where everything holds is a real answer. A gate that can halt a
    send file over a routing decision is one people learn to route around."""
    out = redraft.plan([cold("a", "REJECT"), cold("b", "REJECT")])
    assert out.redraft == []
    assert "never fails a batch" in redraft.report(out)


def test_a_slug_map_and_a_list_both_load():
    """`verdicts.json` in this repo is already a {slug: state} map, so a wave
    written either way has to read the same."""
    as_list = verdict.load([{"slug": "a", "verdict": "SEND"}])
    as_map = verdict.load({"a": {"verdict": "SEND"}})
    assert [v.slug for v in as_list] == [v.slug for v in as_map] == ["a"]
    assert as_map[0].verdict == "SEND"


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
