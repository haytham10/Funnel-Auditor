"""Tests for the log-integrity gate (`crm-gate log`, added 2026-07-26).

The incident: confirmed-send logging is two separate Notion writes — an
`update_content` append to the Email Thread Log, and an `update_properties`
call that increments `Touch #` and rewrites `Notes` — and nothing ties them
together. A 24-lead recovery job found the property write had landed on
every one of them (`Touch #` incremented, `Notes` said "Sent Touch N ...
reconciled by uae-tick") while the log append silently hadn't, so `Touch #`
was claiming sends the page body couldn't back up. Two shapes of the same
bug showed up: a Touch N block missing entirely, and — worse — a LATER
touch logged while an EARLIER one was missing, which a naive "count the
blocks" check would have missed (count matched, sequence didn't).

What is asserted here:

  1. `touch_blocks` re-derives the touch history from the raw page body by
     regex, never from a caller-supplied count — the gate can't be talked
     past by the same actor that might have skipped the append.
  2. A bounced attempt ("Touch #1 attempt ... BOUNCED") does NOT count as a
     real touch; the retry that actually sent does.
  3. A DUPLICATE-labeled block ("... DUPLICATE of Touch #1 ...") does NOT
     count either.
  4. PASS requires the log's touch blocks to be EXACTLY {1, ..., Touch #} —
     catches a missing early touch even when a later one is present (the
     exact shape of the real incident), an over-claimed Touch #, and an
     in-range duplicate.
  5. print_log_integrity's PASS/FAIL line shapes match print_offer/print_send
     (skills quote them verbatim).

Run: python tests/test_log_integrity_gate.py
     (or python -m pytest tests/test_log_integrity_gate.py -q)
"""

import io
import json
import os
import sys
import tempfile
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audit import crm_gate

_LOG_COMPLETE = """## SMYKM Hook
...
## Email Thread Log
[2026-07-20] — Touch #1 — Subject: "x" — Sent
Hey Lead
...
Reply: No reply
Next: Touch 2 due 2026-07-23
2026-07-25 — Touch #2 — Subject: "x" — Sent
Hey Lead
...
Reply: No reply
Next: Awaiting reply.
## Price Discovery
"""

_LOG_MISSING_T1 = """## Email Thread Log
2026-07-25 — Touch #2 — Subject: "x" — Sent
Hey Lead
...
Reply: No reply
Next: Awaiting reply.
## Price Discovery
"""

_LOG_BOUNCE_ONLY = """## Email Thread Log
2026-07-19 — Touch #1 attempt — Subject: "x" — BOUNCED (address not found).
2026-07-25 — Touch #2 — Subject: "y" — Sent
## Price Discovery
"""

_LOG_BOUNCE_THEN_RETRY = """## Email Thread Log
2026-07-19 — Touch #1 attempt — Subject: "x" — BOUNCED (address not found).
2026-07-20 — Touch #1 — Subject: "x" — Sent (retry to verified address)
2026-07-25 — Touch #2 — Subject: "y" — Sent
## Price Discovery
"""

_LOG_DUPLICATE_NOT_COUNTED = """## Email Thread Log
[2026-07-17] — Touch #1 — Subject: "x" — Sent
Reply: No reply
[2026-07-18] — DUPLICATE of Touch #1 — Subject: "x" — Sent (Inbox 1, in error)
Not logged as Touch 2 — no new content, Touch # stays 1.
2026-07-20 — Touch #2 — Subject: "x" — Sent
## Price Discovery
"""


def test_touch_blocks_ignores_bounce_and_duplicate():
    assert crm_gate.touch_blocks(_LOG_BOUNCE_ONLY) == [2]
    assert crm_gate.touch_blocks(_LOG_BOUNCE_THEN_RETRY) == [1, 2]
    assert crm_gate.touch_blocks(_LOG_DUPLICATE_NOT_COUNTED) == [1, 2]


def test_pass_when_log_matches_touch_count():
    ok, problems, notes = crm_gate.check_log_integrity({"Touch #": 2}, _LOG_COMPLETE)
    assert ok, problems
    assert "1, 2" in notes[0]


def test_fails_on_missing_early_touch_even_when_later_touch_present():
    # This is the real incident's exact shape: Touch # = 2, only the T2
    # block is logged. A "count the blocks" check (1 block, expected ~2)
    # might have been mistaken for "one short"; this asserts it names the
    # actual missing touch number, not just a count mismatch.
    ok, problems, notes = crm_gate.check_log_integrity({"Touch #": 2}, _LOG_MISSING_T1)
    assert not ok
    assert "touch 1" in problems[0]


def test_bounce_attempt_does_not_satisfy_the_touch():
    ok, problems, _ = crm_gate.check_log_integrity({"Touch #": 2}, _LOG_BOUNCE_ONLY)
    assert not ok
    assert "touch 1" in problems[0]


def test_retry_after_bounce_satisfies_the_touch():
    ok, problems, notes = crm_gate.check_log_integrity({"Touch #": 2}, _LOG_BOUNCE_THEN_RETRY)
    assert ok, problems


def test_duplicate_block_does_not_inflate_the_count():
    ok, problems, notes = crm_gate.check_log_integrity({"Touch #": 2}, _LOG_DUPLICATE_NOT_COUNTED)
    assert ok, problems


def test_fails_when_log_has_a_touch_past_the_claimed_count():
    ok, problems, _ = crm_gate.check_log_integrity({"Touch #": 1}, _LOG_COMPLETE)
    assert not ok
    assert "Touch #2" in problems[0]


def test_fails_on_in_range_duplicate_block():
    log = _LOG_COMPLETE.replace(
        '2026-07-25 — Touch #2 — Subject: "x" — Sent',
        '2026-07-24 — Touch #2 — Subject: "x" — Sent\n...\nReply: No reply\n'
        '2026-07-25 — Touch #2 — Subject: "x" — Sent',
    )
    ok, problems, _ = crm_gate.check_log_integrity({"Touch #": 2}, log)
    assert not ok
    assert "touch 2" in problems[-1]


def test_fresh_lead_no_touch_number_no_log_passes_trivially():
    ok, problems, notes = crm_gate.check_log_integrity({}, "## Email Thread Log\n## Price Discovery\n")
    assert ok, problems
    assert "none" in notes[0]


def _run_print_log_integrity(row, page_body):
    with tempfile.TemporaryDirectory() as d:
        row_path = os.path.join(d, "row.json")
        body_path = os.path.join(d, "body.md")
        with open(row_path, "w") as f:
            json.dump(row, f)
        with open(body_path, "w") as f:
            f.write(page_body)
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = crm_gate.print_log_integrity(row_path, body_path)
        return rc, buf.getvalue().strip()


def test_print_log_integrity_pass_line_shape():
    rc, line = _run_print_log_integrity({"Contact Name": "Jane Coach", "Touch #": 2}, _LOG_COMPLETE)
    assert rc == 0
    assert line.startswith("CRM GATE (log): PASS — Jane Coach: "), line


def test_print_log_integrity_fail_line_shape():
    rc, line = _run_print_log_integrity({"Contact Name": "Jane Coach", "Touch #": 2}, _LOG_MISSING_T1)
    assert rc == 1
    assert line.startswith("CRM GATE (log): FAIL — Jane Coach: "), line


def test_print_log_integrity_falls_back_to_unnamed_lead():
    rc, line = _run_print_log_integrity({"Touch #": 0}, "## Email Thread Log\n")
    assert rc == 0
    assert "unnamed lead" in line


# --- no-pytest fallback ------------------------------------------------------

if __name__ == "__main__":
    passed = failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                passed += 1
            except AssertionError as e:
                failed += 1
                print(f"FAIL {name}: {e}")
    print(f"{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
