"""The Claude bill, measured: what a batch actually spent, not how many times.

Run: python -m pytest tests/test_usage.py -q
 or: python tests/test_usage.py

This module exists because `2026-08-02-q2` and `2026-08-02-q3` spent about 410M
tokens producing 22 emails and nothing in the repo could say where it went.
`ledger pass` recorded 99 and 185 passes, both accurate and neither an answer: a
pass is an invocation, and an invocation can be 5k tokens or 150k.

Four behaviours are pinned here, each because the obvious shortcut is the bug
that was actually found.

**Deduplicate on `requestId`, last record winning.** A streaming response emits
several records per API call under one id with `output_tokens` growing across
them. Counting records inflates requests 2-4x; keeping the first undercounts
output about 4x. One forensics run published a total that was wrong by $4 before
catching it.

**The orchestrator is a side, not an agent.** 75% of both batches was the main
thread, which `ledger pass` has no record of because nobody reports a pass for
the loop they are typing in. If the split ever stops being computed, the largest
line item goes invisible again.

**An unreadable transcript raises, and never returns zero.** The layout belongs
to the harness and can move under us. A zero would read as "this batch used no
agents" — the dedupe wall's asymmetry in a fourth costume.

**A subagent whose spawn cannot be found is `unattributed` and says so.** Its
tokens still count. Folding it into another agent type, or dropping it, would
both make a gap look like a measurement.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from outbound import metrics, usage


def assistant(request_id: str, *, output: int = 10, read: int = 0,
              write: int = 0, ttl: str = "ephemeral_5m_input_tokens",
              model: str = "claude-opus-5", sidechain: bool = False) -> dict:
    return {"type": "assistant", "requestId": request_id, "isSidechain": sidechain,
            "timestamp": "2026-08-02T10:00:00Z",
            "message": {"model": model,
                        "usage": {"input_tokens": 1, "output_tokens": output,
                                  "cache_read_input_tokens": read,
                                  "cache_creation_input_tokens": write,
                                  "cache_creation": {ttl: write}}}}


def spawn(tool_id: str, agent_id: str, agent_type: str) -> list:
    """The two records that, together, give a subagent file its agent type."""
    return [
        {"type": "assistant", "requestId": f"req-{tool_id}",
         "message": {"model": "claude-opus-5",
                     "usage": {"input_tokens": 1, "output_tokens": 1,
                               "cache_read_input_tokens": 0,
                               "cache_creation_input_tokens": 0},
                     "content": [{"type": "tool_use", "id": tool_id, "name": "Task",
                                  "input": {"subagent_type": agent_type}}]}},
        {"type": "user",
         "message": {"content": [{"type": "tool_result", "tool_use_id": tool_id,
                                  "content": f"launched.\nagentId: {agent_id}\n"}]}},
    ]


def write_jsonl(path: Path, records: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n",
                    encoding="utf-8")


def project(tmp: str, main: list, subs: dict | None = None) -> usage.Sources:
    base = Path(tmp)
    write_jsonl(base / "session.jsonl", main)
    for agent_id, records in (subs or {}).items():
        write_jsonl(base / "session" / "subagents" / f"agent-{agent_id}.jsonl",
                    records)
    return usage.discover(base)


def test_a_streamed_request_is_one_request_and_its_last_output_count():
    """Several records share one requestId with output_tokens growing across
    them. Counting records reported 2,967 requests where there were 1,429, and
    keeping the first record undercounted output by about 4x."""
    with tempfile.TemporaryDirectory() as tmp:
        sources = project(tmp, [assistant("r1", output=5),
                                assistant("r1", output=40),
                                assistant("r1", output=300)])
        turns = usage.read_turns(sources)
        assert len(turns) == 1
        assert turns[0].output_tokens == 300


def test_a_missing_transcript_directory_raises_and_never_returns_zero():
    """A zero would read as "this batch used no agents". Same asymmetry as the
    dedupe wall: a missing record is not a measurement of nothing."""
    with tempfile.TemporaryDirectory() as tmp:
        try:
            usage.discover(Path(tmp) / "not-here")
        except usage.TranscriptsUnreadable as exc:
            assert "not-here" in str(exc)
        else:  # pragma: no cover - the assertion is that this cannot happen
            raise AssertionError("a missing transcript directory returned a total")


def test_a_directory_with_no_transcripts_names_what_it_saw():
    """The layout belongs to the harness. When it moves, say which files were
    there — `replies` sniffs Smartlead's columns for the same reason."""
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "something-else.txt").write_text("x", encoding="utf-8")
        try:
            usage.discover(tmp)
        except usage.TranscriptsUnreadable as exc:
            assert "something-else.txt" in str(exc)
        else:  # pragma: no cover
            raise AssertionError("an unrecognised layout returned a total")


def test_the_orchestrator_is_split_from_the_subagents():
    """The line `ledger pass` cannot express. 75% of both forensics batches was
    the main thread, and nobody reports a pass for the loop they type in."""
    with tempfile.TemporaryDirectory() as tmp:
        sources = project(
            tmp,
            spawn("toolu_1", "aaa", "draft-worker") + [assistant("m1", read=900)],
            {"aaa": [assistant("s1", read=90, sidechain=True)]})
        out = usage.summarise(usage.read_turns(sources), batch="b", sources=sources)
        assert out["orchestrator"]["requests"] == 2      # the spawn turn, and m1
        assert out["subagents"]["requests"] == 1
        assert out["orchestrator"]["tokens"] > out["subagents"]["tokens"]
        assert out["by_agent"]["draft-worker"]["agents"] == 1


def test_an_unmatched_subagent_is_counted_but_named_as_a_gap():
    """Its tokens are real. Folding them into another agent type, or dropping
    them, would both turn a gap into a measurement."""
    with tempfile.TemporaryDirectory() as tmp:
        sources = project(tmp, [assistant("m1")],
                          {"orphan": [assistant("s1", read=50, sidechain=True)]})
        out = usage.summarise(usage.read_turns(sources), sources=sources)
        assert out["by_agent"][usage.UNATTRIBUTED]["agents"] == 1
        assert out["subagents"]["tokens"] > 0
        assert any("could not be matched" in g for g in out["gaps"])


def test_the_cache_write_ttl_split_survives():
    """The main thread wrote at the 1h tier and every subagent at 5m, and the
    two are priced differently. A single cache_write total hides it."""
    with tempfile.TemporaryDirectory() as tmp:
        sources = project(tmp, [assistant("m1", write=100,
                                          ttl="ephemeral_1h_input_tokens")],
                          {"aaa": [assistant("s1", write=40, sidechain=True)]})
        out = usage.summarise(usage.read_turns(sources), sources=sources)
        assert out["totals"]["cache_write_1h"] == 100
        assert out["totals"]["cache_write_5m"] == 40
        assert out["totals"]["cache_write"] == 140


def test_metrics_prints_a_question_mark_for_tokens_and_never_a_zero():
    """The rule this whole module inherits: a count nobody supplied is `?`. A
    zero-filled token line would look exactly like a cheap batch."""
    text = metrics.report(metrics.BatchMetrics(batch="b"))
    assert f"tokens            {metrics.UNKNOWN}" in text
    assert "tokens            0" not in text


def test_tokens_per_email_stays_unknown_until_written_is_supplied():
    """`written` is `?` by default. Dividing by a denominator nobody supplied
    would invent the one number this instrumentation exists to report."""
    out = metrics.BatchMetrics(batch="b")
    metrics.add_usage(out, {"totals": {"tokens": 1_000_000},
                            "orchestrator": {"tokens": 750_000},
                            "subagents": {"tokens": 250_000},
                            "orchestrator_share": 0.75})
    assert out.tokens_total == 1_000_000
    assert out.tokens_per_shipped is metrics.UNKNOWN
    assert f"tokens_per_email  {metrics.UNKNOWN}" in metrics.report(out)

    out.written = 10
    metrics.add_usage(out, {"totals": {"tokens": 1_000_000},
                            "orchestrator": {"tokens": 750_000},
                            "subagents": {"tokens": 250_000},
                            "orchestrator_share": 0.75})
    assert out.tokens_per_shipped == 100_000
    assert "tokens_per_email  100,000" in metrics.report(out)


def test_the_measured_half_is_labelled_apart_from_the_reported_half():
    """Pass counts were typed by an orchestrator; tokens were read out of the
    transcript that billed for them. Printing both with the same confidence is
    what `REPORTED` exists to prevent."""
    out = metrics.BatchMetrics(batch="b")
    metrics.add_passes(out, [{"stage": "draft", "model": "opus", "count": 12}])
    metrics.add_usage(out, {"totals": {"tokens": 500}, "orchestrator": {"tokens": 400},
                            "subagents": {"tokens": 100}, "orchestrator_share": 0.8})
    text = metrics.report(out)
    assert "passes_by_stage   draft 12 — REPORTED, not measured" in text
    assert "tokens            500 — MEASURED" in text
    assert "orchestrator      400 (80%) vs 100 in subagents" in text


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
