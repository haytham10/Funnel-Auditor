"""Tests for the finding-staleness gate (H3, added 2026-07-26).

The Rita Baki case: her 3,200 AED offer was scoped around a booking-flow
leak she had already fixed herself between the walk and the quote
(docs/journal.md, 2026-07-21/25). Ben Pringle's dead thread showed the same
failure mode. The walk is a snapshot; threads run 5-10 days; Gate 0 selects
for coaches active enough to notice and fix things. Nothing previously
re-checked a finding between the walk and the send/quote.

What is asserted here:

  1. `Findings Bank` lines gain an OPTIONAL `verified:YYYY-MM-DD` tag,
     parsed independently of the existing DEPTH tag; legacy lines without it
     still parse (verified=None).
  2. `check_finding_freshness` PASSes only when `verified` is set AND within
     the ceiling; a missing tag, an unparseable date, or an over-ceiling age
     all FAIL, and every failure message names the Rita Baki case.
  3. `crm-gate send` fails on a finding verified 4 days ago (> 3-day ceiling)
     and passes at 3; it checks the RIGHT entry depending on touch/carrier
     (bank #1 for touch 1, the drawn second-finding for touch 2/3, the
     most-recently-sent entry otherwise).
  4. `crm-gate offer` fails on a finding verified 2 days ago (> 1-day
     ceiling) and passes at 1.
  5. Legacy rows with no `Findings Bank` at all stay ungated on freshness,
     same precedent as `--opener-rank`.
  6. `refresh-finding` diffs a freshly-fetched page against stored evidence
     and reports changed/unchanged without itself deciding the finding
     still holds.

Run: python tests/test_finding_staleness.py
     (or python -m pytest tests/test_finding_staleness.py -q)
"""

import os
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audit import crm_gate, send_cap

_CAP = send_cap.CapState(cap=20, set_on=None, valid=True, inbox="Inbox 1")
_BASE = {"Finding Verified": True, "Email": "a@b.com", "Email Verified": True}

# Wednesday, well clear of the Sunday pause and the noon Dubai cutoff.
_NOW = datetime(2026, 7, 22, 9, 0)
_TODAY = send_cap.today(_NOW)  # 2026-07-22


def _bank(verified: str, rank: int = 1, status: str = "UNUSED") -> str:
    return f"{rank}. {status} | DEEP | verified:{verified} | the finding text"


# --- parsing ------------------------------------------------------------

def test_verified_tag_parses():
    entries = crm_gate.parse_findings_bank(_bank("2026-07-20"))
    assert entries[0]["verified"] == "2026-07-20"


def test_missing_verified_tag_parses_as_none():
    entries = crm_gate.parse_findings_bank("1. UNUSED | DEEP | pricing split")
    assert entries[0]["verified"] is None


def test_legacy_line_with_no_depth_or_verified_still_parses():
    entries = crm_gate.parse_findings_bank("1. UNUSED | dead link")
    assert entries[0]["depth"] is None and entries[0]["verified"] is None
    assert entries[0]["finding"] == "dead link"


# --- check_finding_freshness -------------------------------------------

def test_freshness_passes_within_ceiling():
    entry = crm_gate.parse_findings_bank(_bank("2026-07-20"))[0]  # 2 days old
    ok, problems, notes = crm_gate.check_finding_freshness(entry, 3, today=_TODAY)
    assert ok and not problems
    assert any("2 day(s) ago" in n for n in notes)


def test_freshness_fails_past_ceiling():
    entry = crm_gate.parse_findings_bank(_bank("2026-07-18"))[0]  # 4 days old
    ok, problems, notes = crm_gate.check_finding_freshness(entry, 3, today=_TODAY)
    assert not ok
    assert any("4 day(s) ago" in p for p in problems)
    assert any("Rita Baki" in p for p in problems), problems


def test_freshness_fails_on_missing_verified_tag():
    entry = crm_gate.parse_findings_bank("1. UNUSED | DEEP | pricing split")[0]
    ok, problems, _ = crm_gate.check_finding_freshness(entry, 3, today=_TODAY)
    assert not ok
    assert any("no `verified:` date" in p for p in problems)
    assert any("Rita Baki" in p for p in problems)


def test_freshness_fails_on_unparseable_date():
    entry = dict(rank=1, status="UNUSED", depth="DEEP", verified="not-a-date", finding="x")
    ok, problems, _ = crm_gate.check_finding_freshness(entry, 3, today=_TODAY)
    assert not ok
    assert any("unparseable" in p for p in problems)


def test_freshness_fails_on_none_entry():
    ok, problems, _ = crm_gate.check_finding_freshness(None, 3, today=_TODAY)
    assert not ok
    assert any("no Findings Bank entry" in p for p in problems)


def test_freshness_exactly_at_ceiling_passes():
    entry = crm_gate.parse_findings_bank(_bank("2026-07-19"))[0]  # exactly 3 days
    ok, problems, _ = crm_gate.check_finding_freshness(entry, 3, today=_TODAY)
    assert ok, problems


# --- current_finding ------------------------------------------------------

def test_current_finding_is_most_recently_used():
    bank = (
        "1. USED-T1 | SHALLOW | verified:2026-07-10 | opener finding\n"
        "2. USED-T2 | DEEP | verified:2026-07-20 | second finding\n"
        "3. UNUSED | DEEP | verified:2026-07-20 | third finding"
    )
    entry = crm_gate.current_finding({"Findings Bank": bank})
    assert entry["rank"] == 2


def test_current_finding_falls_back_to_bank_one_when_nothing_used():
    bank = "1. UNUSED | DEEP | verified:2026-07-20 | opener finding"
    entry = crm_gate.current_finding({"Findings Bank": bank})
    assert entry["rank"] == 1


def test_current_finding_none_on_empty_bank():
    assert crm_gate.current_finding({"Findings Bank": ""}) is None


# --- crm-gate send --------------------------------------------------------

def _send_touch1(verified, **kw):
    bank = _bank(verified, rank=1)
    row = dict(_BASE, **{"Findings Bank": bank})
    base = dict(row=row, sends_today=1, touch=1, followups_due=0, cap_state=_CAP,
                now=_NOW, opener_rank=1)
    base.update(kw)
    return crm_gate.check_send(**base)


def test_send_touch1_fails_on_four_day_old_finding():
    ok, problems, _ = _send_touch1("2026-07-18")  # 4 days old
    assert not ok
    assert any("Rita Baki" in p for p in problems), problems


def test_send_touch1_passes_on_three_day_old_finding():
    ok, problems, _ = _send_touch1("2026-07-19")  # exactly 3 days old
    assert ok, problems


def test_send_touch2_second_finding_checks_the_drawn_entry():
    bank = (
        "1. USED-T1 | SHALLOW | verified:2026-07-10 | opener finding\n"
        "2. UNUSED | DEEP | verified:2026-07-18 | the second finding\n"
    )
    row = dict(_BASE, **{"Findings Bank": bank})
    ok, problems, _ = crm_gate.check_send(
        row=row, sends_today=1, touch=2, carries="second-finding", cap_state=_CAP, now=_NOW,
    )
    assert not ok
    assert any('bank #2' in p and "Rita Baki" in p for p in problems), problems


def test_send_touch2_leak_fix_offer_checks_current_finding():
    # No new finding drawn (carries leak-fix-offer, not second-finding) — the
    # thread still stands on the most-recently-sent entry, which must also be
    # fresh. Rank 1 was sent 4 days before Touch 2 goes out.
    bank = "1. USED-T1 | SHALLOW | verified:2026-07-18 | opener finding"
    row = dict(_BASE, **{"Findings Bank": bank})
    ok, problems, _ = crm_gate.check_send(
        row=row, sends_today=1, touch=2, carries="leak-fix-offer", cap_state=_CAP, now=_NOW,
    )
    assert not ok
    assert any("Rita Baki" in p for p in problems), problems


def test_send_ungated_on_legacy_row_with_no_bank_at_all():
    row = dict(_BASE, **{"Findings Bank": ""})
    ok, problems, _ = crm_gate.check_send(
        row=row, sends_today=1, touch=1, followups_due=0, cap_state=_CAP, now=_NOW,
    )
    assert ok, problems


# --- crm-gate offer --------------------------------------------------------

def test_offer_fails_on_two_day_old_finding():
    bank = "1. USED-T1 | DEEP | verified:2026-07-20 | opener finding"  # 2 days old
    row = dict(Status="Call Booked", **{"Findings Bank": bank})
    ok, problems, _ = crm_gate.check_offer(row, now=_NOW)
    assert not ok
    assert any("Rita Baki" in p for p in problems), problems


def test_offer_passes_on_one_day_old_finding():
    bank = "1. USED-T1 | DEEP | verified:2026-07-21 | opener finding"  # 1 day old
    row = dict(Status="Call Booked", **{"Findings Bank": bank})
    ok, problems, _ = crm_gate.check_offer(row, now=_NOW)
    assert ok, problems


def test_offer_ungated_on_legacy_row_with_no_bank_at_all():
    row = dict(Status="Call Booked", **{"Findings Bank": ""})
    ok, problems, _ = crm_gate.check_offer(row, now=_NOW)
    assert ok, problems


def test_offer_still_fails_closed_on_earned_right_independent_of_freshness():
    # A fresh finding doesn't bypass the earned-right check — the two gates
    # are independent, both must clear.
    bank = "1. USED-T1 | DEEP | verified:2026-07-21 | opener finding"
    row = dict(Status="Reply Received", **{"Findings Bank": bank})
    ok, problems, _ = crm_gate.check_offer(row, now=_NOW)
    assert not ok
    assert any("has not earned a number" in p for p in problems)


# --- refresh-finding --------------------------------------------------------

def test_refresh_finding_unknown_rank_fails():
    row = {"Findings Bank": _bank("2026-07-20")}
    ok, result = crm_gate.check_refresh_finding(row, 99, "page text", None)
    assert not ok
    assert "does not match" in result["error"]


def test_refresh_finding_no_baseline_reports_no_diff():
    row = {"Findings Bank": _bank("2026-07-20")}
    ok, result = crm_gate.check_refresh_finding(row, 1, "fresh page text", None)
    assert ok
    assert result["changed"] is None
    assert result["diff"] == []


def test_refresh_finding_unchanged_page():
    row = {"Findings Bank": _bank("2026-07-20")}
    ok, result = crm_gate.check_refresh_finding(row, 1, "same text\nline 2", "same text\nline 2")
    assert ok
    assert result["changed"] is False
    assert "unchanged" in result["note"]


def test_refresh_finding_changed_page_reports_diff():
    row = {"Findings Bank": _bank("2026-07-20")}
    ok, result = crm_gate.check_refresh_finding(
        row, 1, "the button now works fine", "the button is broken",
    )
    assert ok
    assert result["changed"] is True
    assert result["diff"]
    assert "changed since" in result["note"]


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
