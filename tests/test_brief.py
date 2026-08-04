"""`brief` is what makes a stage boundary a place to stop and start again.

The tests that matter here are the ones about what it refuses to say. An
observer that fills a gap with a plausible zero is worse than no observer, and
this repo has been burned by exactly that twice — once when `metrics` computed
`hook_yield 0%` off a legal-looking default, and once when twenty CRM rows
passed a check that counted only populated fields.
"""

import json

import pytest

from outbound import brief as br


def _run(tmp_path, **files):
    work = tmp_path / "work"
    work.mkdir()
    for name, data in files.items():
        name = name.replace("__", ".")
        path = work / name
        if isinstance(data, str):
            path.write_text(data, encoding="utf-8")
        else:
            path.write_text(json.dumps(data), encoding="utf-8")
    return work


def test_empty_run_says_nothing_yet(tmp_path):
    work = _run(tmp_path)
    got = br.derive(work, tmp_path / "out")
    assert got.reached == "nothing yet"
    assert "intake" in got.next_command
    assert got.counts.get("raw") is None


def test_derives_the_counts_the_files_prove(tmp_path):
    work = _run(tmp_path,
                BATCH="2026-08-04-t",
                leads__json=[{"slug": "a"}, {"slug": "b"}, {"slug": "c"}],
                clear__json=[{"slug": "a"}, {"slug": "b"}],
                sites__json={"ok": 7, "total": 10},
                draftable__json=[{"slug": "a"}])
    got = br.derive(work, tmp_path / "out")
    assert got.batch == "2026-08-04-t"
    assert got.counts["raw"] == 3
    assert got.counts["after-dedupe"] == 2
    assert got.counts["passed-floors"] == 1
    assert got.counts["tier0-rate"] == 0.7
    # Every derived count names what proved it. A number with no basis is the
    # thing that gets retyped into the CRM and believed for months.
    for flag in ("raw", "after-dedupe", "passed-floors", "tier0-rate"):
        assert got.basis[flag]


def test_warm_is_unknown_not_zero(tmp_path):
    """The inference is available and must not be drawn.

    `dedupe` exits 1 on a warm hit and stops the run, so a `clear.json` on disk
    implies nobody was warm. That is a reasonable-sounding zero, which is the
    only kind this repo has ever been wrong about.
    """
    work = _run(tmp_path, leads__json=[{"slug": "a"}], clear__json=[{"slug": "a"}])
    got = br.derive(work, tmp_path / "out")
    assert got.counts.get("warm") is None
    assert "--warm" not in br.metrics_command(got)


def test_a_note_supplies_what_no_file_can(tmp_path):
    work = _run(tmp_path, leads__json=[{"slug": "a"}])
    br.write_note(work, "warm", "0")
    br.write_note(work, "source-list", "icf-chunk-1")
    got = br.derive(work, tmp_path / "out")
    assert got.counts["warm"] == "0"
    assert got.counts["source-list"] == "icf-chunk-1"
    cmd = br.metrics_command(got)
    assert "--warm 0" in cmd and "--source-list icf-chunk-1" in cmd


def test_an_unknown_note_key_is_refused(tmp_path):
    work = _run(tmp_path)
    with pytest.raises(KeyError):
        br.write_note(work, "hook-yield", "0.52")


def test_metrics_command_omits_what_nothing_proved(tmp_path):
    """An absent flag prints `?`; a zero-filled one is a measurement."""
    work = _run(tmp_path, leads__json=[{"slug": "a"}])
    got = br.derive(work, tmp_path / "out")
    cmd = br.metrics_command(got)
    assert "--raw 1" in cmd
    for absent in ("--warm", "--written", "--rejected", "--passed-floors",
                   "--tier0-rate", "--source-list"):
        assert absent not in cmd


def test_batch_label_is_not_reported_unreadable(tmp_path):
    """`work/BATCH` is a label, not JSON, and every healthy run has one."""
    work = _run(tmp_path, BATCH="2026-08-04-t", leads__json=[{"slug": "a"}])
    got = br.derive(work, tmp_path / "out")
    assert got.unreadable == []


def test_an_unparseable_state_file_is_named_not_skipped(tmp_path):
    work = _run(tmp_path, leads__json="{not json")
    got = br.derive(work, tmp_path / "out")
    assert any("leads.json" in u for u in got.unreadable)


def test_reached_is_the_furthest_stage_not_the_first_gap(tmp_path):
    """A skipped middle stage is normal — a directory list runs on `clear.json`
    and never writes `run.json`. Reporting the first gap as the frontier would
    send a resuming session back to a stage that was correctly not run."""
    work = _run(tmp_path,
                leads__json=[{"slug": "a"}],
                clear__json=[{"slug": "a"}],
                sites__json={"ok": 1, "total": 1},
                identity__json=[{"slug": "a"}])
    got = br.derive(work, tmp_path / "out")
    assert got.reached == "stage 1b — channels"
    assert "email-find" in got.next_command


def test_export_counts_come_from_shipped_not_drafts(tmp_path):
    """`out/shipped.json` is what export actually wrote. `work/drafts.json`
    differs whenever `--rebalance-ps` moved a line, and it is the file that
    once gave every held lead a draft."""
    work = _run(tmp_path, leads__json=[{"slug": "a"}, {"slug": "b"}])
    out = tmp_path / "out"
    out.mkdir()
    (out / "shipped.json").write_text(json.dumps([{"slug": "a"}]), encoding="utf-8")
    (out / "rejected.txt").write_text("b — hook refuted\n", encoding="utf-8")
    got = br.derive(work, out)
    assert got.counts["written"] == 1
    assert got.counts["rejected"] == 1
