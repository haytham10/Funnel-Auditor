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
  6. `refresh-finding` diffs a freshly-fetched page against stored evidence.
     UNCHANGED auto-stamps `verified:` to today via `bump_verified_date`
     (H3c) and hands back the ready-to-write `new_findings_bank`; CHANGED
     never auto-stamps — a human (or the vision pass) has to look first.
  7. Touch >= 2 runs the same freshness + carrier gate whether it's cold
     (2/3) or warm (4+) — the upper bound that used to block warm touches
     from ever reaching this logic is gone (H3b).

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


# --- H7: the opener must be DEEP (2026-07-27) ------------------------------
# Depth shipped 2026-07-26 as ranking guidance and died as an optional field:
# on 2026-07-27 the live CRM had 203 of 225 entries untagged and 8 of 91 leads
# with any DEEP finding. These pin the enforcement that replaced the guidance.

def _t1(bank, rank=1):
    row = dict(_BASE, **{"Findings Bank": bank})
    return crm_gate.check_send(
        row=row, sends_today=0, touch=1, followups_due=0, opener_rank=rank,
        cap_state=_CAP, now=_NOW,
    )


def test_touch1_opener_fails_on_untagged_depth():
    ok, problems, _ = _t1("1. UNUSED | verified:2026-07-22 | some finding")
    assert not ok
    assert any("no DEPTH tag" in p for p in problems), problems


def test_touch1_opener_fails_on_shallow_finding():
    # The whole point: she fixes a shallow finding herself and leaves.
    ok, problems, _ = _t1("1. UNUSED | SHALLOW | verified:2026-07-22 | dead link on pricing page")
    assert not ok
    assert any("is SHALLOW, so it cannot be the opener" in p for p in problems), problems
    assert any("Rita" in p and "Avneet" in p for p in problems), problems


def test_touch1_opener_passes_on_deep_finding():
    ok, problems, notes = _t1("1. UNUSED | DEEP | verified:2026-07-22 | calendar wide open")
    assert ok, problems
    assert any("is DEEP (not self-fixable)" in n for n in notes), notes


def test_depth_gate_does_not_apply_to_warm_touches():
    # Touch 2+ carriers are already constrained by --carries, and a warm
    # thread stands on what was already sent. Scoping this to touch 1 is
    # deliberate; widening it would block every live follow-up.
    row = dict(_BASE, **{"Findings Bank": "1. USED-T1 | SHALLOW | verified:2026-07-22 | dead link"})
    ok, problems, _ = crm_gate.check_send(
        row=row, sends_today=0, touch=2, carries="disambiguating-question",
        cap_state=_CAP, now=_NOW,
    )
    assert ok, problems


# --- refresh-finding routes calendar findings away from the text diff -------

def test_calendar_finding_is_routed_to_calendar_state_not_a_text_diff():
    # A Calendly page is a ~1KB JS shell, so _fetch_page_text pulls nothing
    # and the diff is meaningless in BOTH directions — the dangerous one being
    # "unchanged", which would auto-stamp a finding nobody re-checked.
    bank = "1. UNUSED | DEEP | verified:2026-07-22 | her Calendly has 26 of 30 days wide open"
    ok, result = crm_gate.check_refresh_finding(
        row={"Findings Bank": bank}, rank=1, page_text="", baseline_text="",
    )
    assert ok
    assert result["use_calendar_state"] is True
    assert result["new_findings_bank"] is None, "must not auto-stamp"
    assert "calendar-state" in result["note"]


def test_ordinary_finding_still_takes_the_text_diff():
    bank = "1. UNUSED | DEEP | verified:2026-07-22 | pricing split across 4 platforms"
    ok, result = crm_gate.check_refresh_finding(
        row={"Findings Bank": bank}, rank=1, page_text="same", baseline_text="same",
    )
    assert ok
    assert not result.get("use_calendar_state")
    assert result["changed"] is False
    assert result["new_findings_bank"] is not None


# --- the unparseable-bank hole (2026-07-27) --------------------------------
# "No bank" and "a bank nothing can read" used to be the same thing to the
# gate: both skipped the freshness check silently. Rita Baki's row was the
# second kind while carrying a live 3,200 AED quote on a finding she had
# already fixed. Her real grammar is the fixture.

_RITA_BANK = (
    "1. DEAD (refuted on the 07-25 re-walk) | booking flow leads to a bare form\n"
    "2. DEAD (refuted on the 07-25 re-walk) | discovery call CTA has no scheduler"
)


def test_bank_is_unparseable_detects_ritas_real_grammar():
    assert crm_gate.bank_is_unparseable(_RITA_BANK)


def test_bank_is_unparseable_false_on_empty_and_whitespace():
    # A genuinely empty bank stays ungated — that precedent predates this.
    assert not crm_gate.bank_is_unparseable("")
    assert not crm_gate.bank_is_unparseable("   \n  \n")
    assert not crm_gate.bank_is_unparseable(None)


def test_bank_is_unparseable_false_when_some_lines_parse():
    # Leaving a killed finding in a non-matching grammar is the SANCTIONED way
    # to hide it from the gate without deleting the evidence. One live line is
    # enough; this must not regress into "every line must parse".
    mixed = _RITA_BANK + "\n3. UNUSED | SHALLOW | verified:2026-07-22 | currency split across pages"
    assert not crm_gate.bank_is_unparseable(mixed)


def test_send_fails_closed_on_unparseable_bank():
    row = dict(_BASE, **{"Findings Bank": _RITA_BANK})
    ok, problems, _ = crm_gate.check_send(
        row=row, sends_today=1, touch=1, followups_due=0, cap_state=_CAP, now=_NOW,
    )
    assert not ok
    assert any("not one line parses" in p for p in problems), problems


def test_send_on_mixed_bank_checks_the_line_that_parses():
    # The surviving live finding is fresh, so this passes — proving the mixed
    # bank reached the freshness check instead of being rejected wholesale.
    # DEEP because H7 (below) blocks a SHALLOW touch-1 opener; this test is
    # about the mixed bank reaching the freshness check at all, not depth.
    mixed = _RITA_BANK + "\n3. UNUSED | DEEP | verified:2026-07-22 | pricing split across platforms"
    row = dict(_BASE, **{"Findings Bank": mixed})
    ok, problems, _ = crm_gate.check_send(
        row=row, sends_today=1, touch=1, followups_due=0, opener_rank=3,
        cap_state=_CAP, now=_NOW,
    )
    assert ok, problems


# --- H3b: warm touches (4+) reach the same gate, not just cold 1/2/3 -------
# Regression for the exact shape of the Rita Baki incident: her real send was
# a WARM bump (Touch 5), which the gate never saw because `touch >
# COLD_SEQUENCE_TOUCHES` used to hard-reject before reaching the freshness
# check at all.

def test_send_touch_zero_is_invalid():
    row = dict(_BASE, **{"Findings Bank": ""})
    ok, problems, _ = crm_gate.check_send(row=row, sends_today=0, touch=0, cap_state=_CAP, now=_NOW)
    assert not ok
    assert any("not a valid touch number" in p for p in problems)


def test_send_warm_touch_five_reaches_freshness_check():
    bank = "1. USED-T1 | SHALLOW | verified:2026-07-18 | opener finding"  # 4 days old
    row = dict(_BASE, **{"Findings Bank": bank})
    ok, problems, _ = crm_gate.check_send(
        row=row, sends_today=1, touch=5, carries="disambiguating-question",
        cap_state=_CAP, now=_NOW,
    )
    assert not ok
    assert any("Rita Baki" in p for p in problems), problems


def test_send_warm_touch_six_passes_on_a_fresh_finding():
    bank = "1. USED-T1 | SHALLOW | verified:2026-07-21 | opener finding"  # 1 day old
    row = dict(_BASE, **{"Findings Bank": bank})
    ok, problems, _ = crm_gate.check_send(
        row=row, sends_today=1, touch=6, carries="leak-fix-offer", cap_state=_CAP, now=_NOW,
    )
    assert ok, problems


def test_send_warm_touch_still_requires_a_carrier():
    # Untouched by H3b, but worth locking down: warm touches run the SAME
    # generic touch>=2 branch as cold 2/3, so a bare warm bump still fails —
    # it was never special-cased to "2 or 3 only" in the first place.
    bank = "1. USED-T1 | SHALLOW | verified:2026-07-21 | opener finding"
    row = dict(_BASE, **{"Findings Bank": bank})
    ok, problems, _ = crm_gate.check_send(
        row=row, sends_today=1, touch=5, cap_state=_CAP, now=_NOW,
    )
    assert not ok
    assert any("must declare what new thing it carries" in p for p in problems)


# --- day-boundary fix: a rolled touch-1 opener checks freshness as of the
# day it actually LEAVES (tomorrow, post-cutoff), not the day it was queued
# -----------------------------------------------------------------------

def test_send_touch1_post_cutoff_checks_freshness_against_send_day_not_today():
    # Post-noon Dubai: this opener is scheduled for TOMORROW (2026-07-23).
    # The finding is 3 days old as of TODAY (2026-07-22) — inside the
    # ceiling if freshness were (wrongly) checked against today — but 4
    # days old as of tomorrow, when it actually leaves. Must FAIL.
    after_noon = datetime(2026, 7, 22, 14, 0)
    bank = "1. UNUSED | DEEP | verified:2026-07-19 | opener finding"
    row = dict(_BASE, **{"Findings Bank": bank})
    ok, problems, _ = crm_gate.check_send(
        row=row, sends_today=1, touch=1, followups_due=0, opener_rank=1,
        sends_next_day=0, cap_state=_CAP, now=after_noon,
    )
    assert not ok
    assert any("4 day(s) ago" in p and "Rita Baki" in p for p in problems), problems


def test_send_touch1_post_cutoff_passes_when_fresh_as_of_send_day():
    after_noon = datetime(2026, 7, 22, 14, 0)
    bank = "1. UNUSED | DEEP | verified:2026-07-20 | opener finding"  # 3 days as of tomorrow
    row = dict(_BASE, **{"Findings Bank": bank})
    ok, problems, _ = crm_gate.check_send(
        row=row, sends_today=1, touch=1, followups_due=0, opener_rank=1,
        sends_next_day=0, cap_state=_CAP, now=after_noon,
    )
    assert ok, problems


# --- crm-gate offer --------------------------------------------------------

def test_offer_has_no_freshness_ceiling_at_all():
    # STALE_OFFER_DAYS was removed 2026-07-27 with The First Five: the offer
    # no longer quotes work scoped around the finding, so a stale finding has
    # nothing to misprice. A finding old enough to fail the SEND gate twice
    # over must still clear the offer gate.
    bank = "1. USED-T1 | DEEP | verified:2026-07-01 | opener finding"  # 21 days old
    row = dict(Status="Call Booked", **{"Findings Bank": bank})
    ok, problems, _ = crm_gate.check_offer(row, now=_NOW)
    assert ok, problems
    assert not hasattr(crm_gate, "STALE_OFFER_DAYS")


def test_offer_ungated_on_unparseable_bank_too():
    # check_offer stopped reading the bank entirely, so the unparseable-bank
    # hard fail is a SEND-gate rule only. Pinned so nobody "restores symmetry"
    # by adding a check the offer gate has no use for.
    row = dict(Status="Call Booked", **{"Findings Bank": "1. DEAD (refuted 07-25) | old finding"})
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


# --- bump_verified_date ------------------------------------------------

def test_bump_verified_date_updates_only_the_target_rank():
    bank = (
        "1. USED-T1 | SHALLOW | verified:2026-07-10 | opener finding\n"
        "2. UNUSED | DEEP | verified:2026-07-10 | second finding"
    )
    new_bank = crm_gate.bump_verified_date(bank, 2, "2026-07-26")
    entries = crm_gate.parse_findings_bank(new_bank)
    assert entries[0]["verified"] == "2026-07-10"  # untouched
    assert entries[1]["verified"] == "2026-07-26"
    assert entries[1]["status"] == "UNUSED" and entries[1]["depth"] == "DEEP"
    assert entries[1]["finding"] == "second finding"


def test_bump_verified_date_inserts_tag_when_missing():
    bank = "1. UNUSED | DEEP | pricing split"  # no verified: tag at all
    new_bank = crm_gate.bump_verified_date(bank, 1, "2026-07-26")
    entries = crm_gate.parse_findings_bank(new_bank)
    assert entries[0]["verified"] == "2026-07-26"
    assert entries[0]["finding"] == "pricing split"


def test_bump_verified_date_unknown_rank_raises():
    try:
        crm_gate.bump_verified_date(_bank("2026-07-20", rank=1), 5, "2026-07-26")
        assert False, "expected ValueError"
    except ValueError as e:
        assert "rank 5" in str(e)


# --- refresh-finding --------------------------------------------------------

def test_refresh_finding_unknown_rank_fails():
    row = {"Findings Bank": _bank("2026-07-20")}
    ok, result = crm_gate.check_refresh_finding(row, 99, "page text", None)
    assert not ok
    assert "does not match" in result["error"]


def test_refresh_finding_no_baseline_reports_no_diff_and_no_stamp():
    row = {"Findings Bank": _bank("2026-07-20")}
    ok, result = crm_gate.check_refresh_finding(row, 1, "fresh page text", None)
    assert ok
    assert result["changed"] is None
    assert result["diff"] == []
    assert result["new_findings_bank"] is None


def test_refresh_finding_unchanged_page_auto_stamps():
    row = {"Findings Bank": _bank("2026-07-20")}
    ok, result = crm_gate.check_refresh_finding(
        row, 1, "same text\nline 2", "same text\nline 2", today="2026-07-26",
    )
    assert ok
    assert result["changed"] is False
    assert "unchanged" in result["note"]
    assert result["new_findings_bank"] is not None
    entries = crm_gate.parse_findings_bank(result["new_findings_bank"])
    assert entries[0]["verified"] == "2026-07-26"
    assert "verbatim" in result["note"]


def test_refresh_finding_changed_page_never_auto_stamps():
    row = {"Findings Bank": _bank("2026-07-20")}
    ok, result = crm_gate.check_refresh_finding(
        row, 1, "the button now works fine", "the button is broken", today="2026-07-26",
    )
    assert ok
    assert result["changed"] is True
    assert result["diff"]
    assert result["new_findings_bank"] is None
    assert "NOT auto-stamped" in result["note"]


def test_print_refresh_finding_requires_url_or_page_file(tmp_path=None):
    import json as _json
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        row_path = f"{tmp}/row.json"
        with open(row_path, "w") as f:
            _json.dump({"Findings Bank": _bank("2026-07-20")}, f)
        rc = crm_gate.print_refresh_finding(row_path, 1)
        assert rc == 1


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
