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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audit import crm_gate, send_cap

_CAP = send_cap.CapState(cap=20, set_on=None, valid=True, inbox="Inbox 1")
_BASE = {"Finding Verified": True, "Email": "a@b.com", "Email Verified": True}

_TAGGED = (
    "1. UNUSED | SHALLOW | checkout 404s on mobile\n"
    "2. UNUSED | DEEP | pricing split across 4 platforms\n"
    "3. RESERVED | DEEP | whole program readable free\n"
    "4. USED-T1 | SHALLOW | stale cohort dates"
)
_LEGACY = "1. UNUSED | dead link\n2. UNUSED | no pricing shown"
_ONLY_SHALLOW = "1. UNUSED | SHALLOW | dead link\n2. UNUSED | SHALLOW | typo"
_DEEP_UNRESERVED = "1. UNUSED | DEEP | pricing\n2. UNUSED | DEEP | no owned capture"


def _send(bank, **kw):
    row = dict(_BASE, **{"Findings Bank": bank})
    base = dict(row=row, sends_today=5, touch=2, carries="second-finding", cap_state=_CAP)
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
