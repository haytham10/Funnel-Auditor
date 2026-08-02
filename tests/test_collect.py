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
