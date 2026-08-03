"""State files assembled by code, and failing closed when a member is missing.

Run: python -m pytest tests/test_collect.py -q
 or: python tests/test_collect.py

`work/researched.json`, `work/draftable.json` and `work/drafts.json` were written
by no command. The orchestrator serialised each one out of its own context, which
is the most expensive way to concatenate JSON — the parts are already in a
600k-token window, the whole is emitted as output, and then read back in as a
tool result. It also made every stage unresumable: a file that exists only
because somebody remembered to write it cannot be picked up by anything that was
not there when it happened.

The coverage check is `crm-rows`' lesson, not a new idea. Twenty CRM rows once
went in with no First Name, Last Name, Website, LinkedIn or City on any of them,
and the check that passed them looked at four populated fields and reported
20/20. A count of what was found is not a count of what should exist.
"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from outbound import collect


def drafts(tmp, slugs):
    for slug in slugs:
        (Path(tmp) / f"draft-{slug}.json").write_text(
            json.dumps({"slug": slug, "subject": "s"}), encoding="utf-8")


def test_found_six_and_found_six_of_seventeen_are_different_answers():
    """The whole value of the check. `crm-rows` reported 20/20 on rows missing
    five columns because it counted what was there."""
    with tempfile.TemporaryDirectory() as tmp:
        drafts(tmp, ["a", "b"])
        got = collect.collect(tmp, "drafts", expect=["a", "b", "c"])
        assert len(got.members) == 2
        assert got.missing == ["c"]
        assert collect.failed(got)
        assert "MISSING  c" in collect.report(got)


def test_a_complete_stage_passes():
    with tempfile.TemporaryDirectory() as tmp:
        drafts(tmp, ["a", "b"])
        got = collect.collect(tmp, "drafts", expect=["a", "b"])
        assert not collect.failed(got) and got.missing == []


def test_an_empty_stage_fails_rather_than_writing_an_empty_file():
    """A stage that collected nothing did not run. Writing `[]` and exiting 0
    would hand the next stage a file that looks like a real answer."""
    with tempfile.TemporaryDirectory() as tmp:
        got = collect.collect(tmp, "drafts")
        assert collect.failed(got)
        assert "did not run" in collect.report(got)


def test_an_unreadable_member_is_named_and_fails_closed():
    """A run that died mid-write leaves one. Silently skipping it would drop a
    lead out of the batch with nothing anywhere saying so."""
    with tempfile.TemporaryDirectory() as tmp:
        drafts(tmp, ["a"])
        (Path(tmp) / "draft-broken.json").write_text("{not json", encoding="utf-8")
        got = collect.collect(tmp, "drafts")
        assert got.skipped and "draft-broken.json" in got.skipped[0]
        assert collect.failed(got)


def test_a_slice_holding_an_array_contributes_every_member():
    """`research-worker` returns a slice of about ten leads as one array, so a
    slice file is not one lead."""
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "research-1.json").write_text(json.dumps(
            [{"slug": "a", "passes_floors": True},
             {"slug": "b", "passes_floors": True}]), encoding="utf-8")
        got = collect.collect(tmp, "research")
        assert len(got.members) == 2 and len(got.files) == 1


def test_draftable_keeps_only_what_passed_the_floors():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "research-1.json").write_text(json.dumps(
            [{"slug": "a", "passes_floors": True},
             {"slug": "b", "passes_floors": False, "failed_floors": ["uae_based"]}]),
            encoding="utf-8")
        got = collect.collect(tmp, "draftable")
        assert [r["slug"] for r in got.members] == ["a"]


def test_the_written_file_is_the_list_the_next_stage_reads():
    with tempfile.TemporaryDirectory() as tmp:
        drafts(tmp, ["a", "b"])
        got = collect.collect(tmp, "drafts")
        target = collect.write(got)
        assert [r["slug"] for r in json.loads(target.read_text())] == ["a", "b"]


# ------------------------------------------------- the hook verdicts, merged


def _research_row(slug="coach-zee", **over):
    row = {"slug": slug, "name": "Coach Zee", "hook_verified": "proposed",
           "observations": [{"url": "https://instagram.com/p/X"}]}
    row.update(over)
    return row


def _write(dirpath, name, payload):
    import json as _json
    (Path(dirpath) / name).write_text(_json.dumps(payload), encoding="utf-8")


def test_a_verdict_lands_on_the_research_object():
    """The skill has said "merge them in one step" since the verifier got Write,
    and nothing did it — so a verified batch read `hook_verified: proposed` and
    `metrics` computed hook_yield 0% off a legal-looking value."""
    from outbound import collect

    with tempfile.TemporaryDirectory() as where:
        rows = [_research_row()]
        _write(where, "hookverdict-zee.json",
               {"slug": "zee", "verdict": "VERIFIED",
                "resolved_hook": "your picks from this year's photos.",
                "quote_found": "3 or 4 are my fav",
                "hook_source_url": "https://instagram.com/p/X",
                "hook_date": "2026-07-31"})
        _write(where, "hook-zee.json", {"hook_type": "LIFE",
                                        "observation_id": "abc123"})
        assert collect.merge_hooks(Path(where), rows) == []
        assert rows[0]["hook_verified"] == "verified"
        assert rows[0]["hook"] == "your picks from this year's photos."
        assert rows[0]["hook_type"] == "LIFE"
        assert rows[0]["observation_id"] == "abc123"


def test_a_refuted_verdict_writes_the_status_and_not_the_hook():
    """Keeping the text an independent reader refused would leave the field a
    drafter reads populated and the field a gate reads failing."""
    from outbound import collect

    with tempfile.TemporaryDirectory() as where:
        rows = [_research_row(hook="something certified by nobody")]
        _write(where, "hookverdict-zee.json",
               {"slug": "zee", "verdict": "REFUTED",
                "resolved_hook": "something certified by nobody"})
        collect.merge_hooks(Path(where), rows)
        assert rows[0]["hook_verified"] == "refuted"
        assert rows[0]["hook"] == ""


def test_an_ambiguous_verdict_is_refused_rather_than_placed():
    """Merging a certification onto the wrong lead ships a verified hook about
    somebody else — the one mistake in this file that reaches a reader."""
    from outbound import collect

    with tempfile.TemporaryDirectory() as where:
        rows = [_research_row("coach-zee"), _research_row("zee-coaching")]
        _write(where, "hookverdict-zee.json",
               {"slug": "zee", "verdict": "VERIFIED", "resolved_hook": "x"})
        problems = collect.merge_hooks(Path(where), rows)
        assert problems and "2 research object(s)" in problems[0]
        assert all(r["hook_verified"] == "proposed" for r in rows)


def test_an_empty_proposal_records_a_null_hook_rather_than_a_pending_one():
    """A worker that looked and wrote no hook has answered. `proposed` reads
    like a lead nobody got to."""
    from outbound import collect

    with tempfile.TemporaryDirectory() as where:
        rows = [_research_row("kayleigh-green")]
        _write(where, "hook-kayleigh-green.json", [])
        collect.merge_hooks(Path(where), rows)
        assert rows[0]["hook_verified"] == "none"


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
