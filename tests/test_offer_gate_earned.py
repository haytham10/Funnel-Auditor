"""Tests for the re-gated offer gate (2026-07-24).

The old rule blocked every priced offer until a verbatim `Price Discovery
Answer` was logged AND a `Discovery Anchor` was set. That rule was the
track's founding premise and it has been falsified: 100 touched leads, the
question asked 3 times, 3 answers, all `Refused to name`, 0 numbers named.
The gate stopped collecting data and started blocking money emails to leads
who had explicitly asked for a price.

What is asserted here:

  1. The gate now PASSes on EARNED RIGHT, by either of two routes — an earned
     `Status`, or the `Asked For Price` checkbox.
  2. A lead who has earned neither still FAILs, and the failure names both
     routes so the operator knows how to unblock it.
  3. `Price Discovery Answer` / `Discovery Anchor` are ADVISORY: they appear
     as notes, and their absence never blocks (the regression that matters).
  4. `Refused to name` emits a WARNING note — a trust signal, not a price
     signal — so the offer email leads with the guarantees, not a discount.
  5. check_offer returns a 3-tuple (ok, problems, notes), matching check_send,
     and print_offer's PASS/FAIL line shapes are unchanged (skills quote them).

Run: python tests/test_offer_gate_earned.py
     (or python -m pytest tests/test_offer_gate_earned.py -q)
"""

import json
import os
import sys
import tempfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audit import crm_gate

_BASE = {"Contact Name": "Jane Coach"}


def _row(**over):
    row = dict(_BASE)
    row.update(over)
    return row


def _run_print_offer(row):
    """print_offer over a temp row dump. Returns (exit_code, printed_line)."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "row.json"
        path.write_text(json.dumps(row))
        buf = StringIO()
        with redirect_stdout(buf):
            rc = crm_gate.print_offer(path)
    return rc, buf.getvalue().strip()


# --- route (a): earned by status --------------------------------------------

def test_earned_by_status_passes():
    ok, problems, notes = crm_gate.check_offer(_row(Status="Call Booked"))
    assert ok, problems
    assert not problems
    assert any('earned by status "Call Booked"' in n for n in notes), notes


def test_every_earned_status_passes():
    # Status is a single select and forward progress overwrites, so the whole
    # set has to pass — a lead at `Won` was necessarily at `Offer Sent` first.
    for status in crm_gate.EARNED_STATUSES:
        ok, problems, _ = crm_gate.check_offer(_row(Status=status))
        assert ok, f"{status} should earn a number: {problems}"


def test_leak_fix_statuses_are_in_the_earned_set():
    # The paid Leak Fix is the rung that earns the Sprint offer. If these
    # statuses ever drop out of the set, a paying customer gets blocked.
    assert "Leak Fix Sold" in crm_gate.EARNED_STATUSES
    assert "Leak Fix Delivered" in crm_gate.EARNED_STATUSES


# --- route (b): earned by ask -----------------------------------------------

def test_earned_by_checkbox_passes():
    row = _row(Status="Reply Received", **{"Asked For Price": "__YES__"})
    ok, problems, notes = crm_gate.check_offer(row)
    assert ok, problems
    assert any("earned by ask" in n for n in notes), notes


def test_earned_by_checkbox_accepts_every_truthy_shape():
    for value in (True, "__YES__", "Yes", "true", "checked"):
        row = _row(Status="Reply Received", **{"Asked For Price": value})
        ok, problems, _ = crm_gate.check_offer(row)
        assert ok, f"{value!r} should read as checked: {problems}"


def test_unchecked_ask_does_not_earn():
    row = _row(Status="Reply Received", **{"Asked For Price": "__NO__"})
    ok, _, _ = crm_gate.check_offer(row)
    assert not ok


# --- neither route: fails closed --------------------------------------------

def test_unearned_fails_naming_both_routes():
    ok, problems, _ = crm_gate.check_offer(_row(Status="Reply Received"))
    assert not ok
    assert any("has not earned a number" in p for p in problems), problems
    joined = " ".join(problems)
    assert "Asked For Price" in joined
    assert "Status" in joined


def test_unearned_fails_closed_on_missing_properties():
    ok, problems, _ = crm_gate.check_offer(_row())
    assert not ok
    assert any("unset" in p for p in problems), problems


# --- the falsified rule: answer/anchor are advisory now ----------------------

def test_price_discovery_answer_no_longer_blocks():
    # THE regression. This exact row FAILED under the old rule.
    ok, problems, _ = crm_gate.check_offer(_row(Status="Offer Sent"))
    assert ok, problems


def test_missing_answer_is_an_advisory_note_only():
    ok, problems, notes = crm_gate.check_offer(_row(Status="Offer Sent"))
    assert ok
    assert problems == []
    assert any("pricing without their number" in n for n in notes), notes


def test_logged_answer_reported_as_char_count():
    answer = "we'd go to about 3k AED"
    row = _row(Status="Won", **{"Price Discovery Answer": answer})
    ok, _, notes = crm_gate.check_offer(row)
    assert ok
    assert any(f"discovery answer logged ({len(answer)} chars)" in n for n in notes), notes


def test_not_asked_yet_anchor_is_advisory_not_a_block():
    row = _row(Status="Offer Sent", **{"Discovery Anchor": "Not asked yet"})
    ok, problems, notes = crm_gate.check_offer(row)
    assert ok, problems
    assert any("no Discovery Anchor set" in n for n in notes), notes


# --- the trust-signal warning ------------------------------------------------

def test_refused_to_name_emits_trust_warning():
    row = _row(Status="Call Booked", **{"Discovery Anchor": "Refused to name"})
    ok, _, notes = crm_gate.check_offer(row)
    assert ok
    warning = [n for n in notes if "WARNING" in n]
    assert warning, notes
    assert "TRUST signal" in warning[0]
    assert "guarantee" in warning[0]


def test_normal_anchor_is_a_plain_note_not_a_warning():
    row = _row(Status="Call Booked", **{"Discovery Anchor": "At 735 AED"})
    ok, _, notes = crm_gate.check_offer(row)
    assert ok
    assert any('anchor "At 735 AED"' in n for n in notes), notes
    assert not any("WARNING" in n for n in notes), notes


# --- contract + printed line shapes ------------------------------------------

def test_check_offer_returns_three_tuple():
    result = crm_gate.check_offer(_row(Status="Won"))
    assert len(result) == 3
    assert isinstance(result[1], list) and isinstance(result[2], list)


def test_print_offer_pass_line_shape():
    rc, line = _run_print_offer(_row(Status="Call Booked"))
    assert rc == 0
    assert line.startswith("CRM GATE (offer): PASS — Jane Coach: "), line
    assert ", " in line


def test_print_offer_fail_line_shape():
    rc, line = _run_print_offer(_row(Status="Reply Received"))
    assert rc == 1
    assert line.startswith("CRM GATE (offer): FAIL — Jane Coach: "), line


def test_print_offer_falls_back_to_unnamed_lead():
    rc, line = _run_print_offer({"Status": "Won"})
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
