"""Tests for finding-depth tiers + bait-and-reserve in the Findings Bank
(Problem 1):

  1. The bank line gains an OPTIONAL depth tag and a RESERVED status:
     `N. STATUS | DEPTH | finding`. Legacy `N. STATUS | finding` rows must
     still parse identically (depth=None) so live rows gate exactly as before.
  2. next_unused_finding never draws a RESERVED entry — the deep call-bait is
     held out of email, so `--carries second-finding` can never spend it.
  3. reserved_deep_finding surfaces the held finding.
  4. check_send emits reserve / low-value notes (never hard fails), and stays
     silent on legacy untagged banks.

Run: python tests/test_findings_bank_depth.py
     (or python -m pytest tests/test_findings_bank_depth.py -q)
"""

import os
import sys
from datetime import datetime as _datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audit import crm_gate, send_cap

_CAP = send_cap.CapState(cap=20, set_on=None, valid=True, inbox="Inbox 1")
_BASE = {"Finding Verified": True, "Email": "a@b.com", "Email Verified": True}

# Fixed "now" for every test in this file, so the fixtures' `verified:` tags
# (2 days earlier — inside the 3-day send ceiling) gate deterministically
# regardless of when the suite actually runs. Also doubles as the touch-1
# opener tests' pre-noon-Dubai instant (side-steps the send-day-rollover branch).
_NOW = _datetime(2026, 7, 24, 9, 0)

_TAGGED = (
    "1. UNUSED | SHALLOW | verified:2026-07-22 | checkout 404s on mobile\n"
    "2. UNUSED | DEEP | verified:2026-07-22 | pricing split across 4 platforms\n"
    "3. RESERVED | DEEP | verified:2026-07-22 | whole program readable free\n"
    "4. USED-T1 | SHALLOW | verified:2026-07-22 | stale cohort dates"
)
# _TAGGED models a PRE-2026-07-27 walked row, with UNUSED entries that were
# once email material. Rows walked since then are all-RESERVED (see
# _ALL_RESERVED below). Both shapes must keep parsing and gating.
_LEGACY = (
    "1. UNUSED | verified:2026-07-22 | dead link\n"
    "2. UNUSED | verified:2026-07-22 | no pricing shown"
)
_ONLY_SHALLOW = (
    "1. UNUSED | SHALLOW | verified:2026-07-22 | dead link\n"
    "2. UNUSED | SHALLOW | verified:2026-07-22 | typo"
)
_DEEP_UNRESERVED = (
    "1. UNUSED | DEEP | verified:2026-07-22 | pricing\n"
    "2. UNUSED | DEEP | verified:2026-07-22 | no owned capture"
)


def _send(bank, **kw):
    row = dict(_BASE, **{"Findings Bank": bank})
    base = dict(row=row, sends_today=5, touch=2, carries="call-ask", cap_state=_CAP,
                now=_NOW)
    base.update(kw)
    return crm_gate.check_send(**base)


# --- parsing ----------------------------------------------------------------

def test_parse_tagged_line_captures_depth_and_reserved():
    entries = crm_gate.parse_findings_bank(_TAGGED)
    assert [e["depth"] for e in entries] == ["SHALLOW", "DEEP", "DEEP", "SHALLOW"]
    assert [e["status"] for e in entries] == ["UNUSED", "UNUSED", "RESERVED", "USED-T1"]
    assert entries[0]["finding"] == "checkout 404s on mobile"


def test_legacy_line_parses_with_depth_none():
    entries = crm_gate.parse_findings_bank(_LEGACY)
    assert len(entries) == 2
    assert all(e["depth"] is None for e in entries)
    assert entries[1]["finding"] == "no pricing shown"


# --- reserve is never drawn -------------------------------------------------

def test_next_unused_skips_reserved():
    row = {"Findings Bank": _TAGGED}
    entry = crm_gate.next_unused_finding(row)
    assert entry is not None and entry["rank"] == 2 and entry["status"] == "UNUSED"
    # the RESERVED deep finding at rank 3 is never returned
    assert entry["finding"] != "whole program readable free"


def test_reserved_deep_finding_found_and_absent():
    assert crm_gate.reserved_deep_finding({"Findings Bank": _TAGGED})["rank"] == 3
    assert crm_gate.reserved_deep_finding({"Findings Bank": _LEGACY}) is None


# --- notes (never hard fails) -----------------------------------------------

def test_reserve_note_present_when_held():
    ok, problems, notes = _send(_TAGGED)
    assert ok and not problems
    assert any("held in reserve" in n for n in notes)


def test_low_value_warning_when_no_deep():
    ok, problems, notes = _send(_ONLY_SHALLOW)
    assert ok and not problems  # still sendable, just flagged
    assert any("low-value" in n for n in notes)


def test_warns_when_deep_present_but_none_reserved():
    ok, problems, notes = _send(_DEEP_UNRESERVED)
    assert ok
    assert any("none is marked RESERVED" in n for n in notes)


def test_legacy_bank_stays_silent():
    ok, problems, notes = _send(_LEGACY)
    assert ok
    assert not any("low-value" in n or "reserve" in n.lower() for n in notes)


# --- cold-read: touch 1 declares which sanctioned pattern it was built from.
# Replaced the --opener-rank block on 2026-07-27, when the opener stopped being
# a finding. That check was the regression for the 2026-07-24 Tracy Harmoush
# incident (a draft built from the page-body narrative instead of the bank
# order, emailing the exact finding the bank had reserved as call bait). The
# incident is impossible now — nothing emails a finding — but the
# declare-what-you-drafted discipline is kept and re-pointed. -----------------

_BEFORE_NOON_DUBAI = _NOW  # side-step the noon cutoff branch (same fixed instant as _send's _NOW)

# What a walked row looks like now: every finding is call bait.
_ALL_RESERVED = (
    "1. RESERVED | DEEP | verified:2026-07-22 | pricing split across 4 platforms\n"
    "2. RESERVED | DEEP | verified:2026-07-22 | whole program readable free\n"
    "3. RESERVED | SHALLOW | verified:2026-07-22 | checkout 404s on mobile"
)


def _opener(bank, cold_read=None, **kw):
    row = dict(_BASE, **{"Findings Bank": bank})
    base = dict(row=row, sends_today=1, touch=1, followups_due=0, cap_state=_CAP,
                now=_BEFORE_NOON_DUBAI, cold_read=cold_read)
    base.update(kw)
    return crm_gate.check_send(**base)


def test_cold_read_required_on_touch_1():
    ok, problems, notes = _opener(_ALL_RESERVED)
    assert not ok
    assert any("--cold-read is required" in p for p in problems), problems


def test_unsanctioned_cold_read_fails():
    # Same rule as "never invent findings": a pattern that is not on the list
    # does not go in an email.
    ok, problems, notes = _opener(_ALL_RESERVED, cold_read="coaches-are-busy")
    assert not ok
    assert any("is not a sanctioned pattern" in p for p in problems), problems


def test_all_reserved_bank_passes_touch_1_with_a_cold_read():
    # THE regression for this whole change. Before 2026-07-27 an all-RESERVED
    # bank could not pass touch 1 at all — three independent vetoes fired
    # (--opener-rank required, the rank is RESERVED, and opener_finding()
    # returned None so freshness failed on "no entry to check"). A walked lead
    # is now all-RESERVED by definition, so if this ever goes red again the
    # entire cold pipeline is blocked.
    ok, problems, notes = _opener(_ALL_RESERVED, cold_read="price-invisible")
    assert ok, problems
    assert any('cold read "price-invisible"' in n for n in notes), notes


def test_touch_1_does_not_freshness_check_a_finding_it_never_sends():
    # The findings here are 3 weeks stale and the opener still passes: touch 1
    # cites no finding, so there is nothing for a stale one to misstate. Warm
    # touches still get the ceiling (see test_finding_staleness.py).
    stale = "1. RESERVED | DEEP | verified:2026-07-01 | pricing split across 4 platforms"
    ok, problems, notes = _opener(stale, cold_read="no-aed")
    assert ok, problems


def test_cold_read_still_required_on_a_row_with_no_bank():
    # Unlike --opener-rank, this does NOT depend on the bank: the pattern is a
    # property of the draft, not of the row.
    ok, problems, notes = _opener("", cold_read=None)
    assert not ok
    assert any("--cold-read is required" in p for p in problems), problems

    ok, problems, notes = _opener("", cold_read="rented-audience")
    assert ok, problems


def test_cold_reads_list_matches_the_reference_doc():
    # The gate's list and the drafter's list must never disagree — the doc is
    # what a human reads, the tuple is what the gate enforces.
    from pathlib import Path
    doc = Path(__file__).resolve().parents[1] / (
        ".claude/skills/haytham-email-draft/references/cold-reads.md"
    )
    text = doc.read_text()
    for pattern in crm_gate.COLD_READS:
        assert f"## `{pattern}`" in text, f"{pattern} is gated but undocumented"


def test_opener_finding_helper_returns_lowest_unused_rank():
    entry = crm_gate.opener_finding({"Findings Bank": _TAGGED})
    assert entry is not None and entry["rank"] == 1
    assert entry["finding"] == "checkout 404s on mobile"


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
