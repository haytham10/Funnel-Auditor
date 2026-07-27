"""Tests for the noon-Dubai send-day cutoff (bug #2):

A cold opener queued after noon Dubai can't leave today — it is scheduled for
tomorrow morning — so the send gate attributes it to TOMORROW's send-day and
gates it against tomorrow's ceiling (tomorrow's already-scheduled count), not
today's already-spent one. Follow-ups and warm replies are never rolled: they
still go out today and count against today.

Covers:
  1. send_cap.send_day() / is_after_send_cutoff() — the noon boundary.
  2. crm_gate.check_send touch 1 — before noon behaves as before (today's
     count); after noon requires and uses --sends-next-day (tomorrow).
  3. touch 2/3 (follow-ups) are unaffected by the cutoff.

Run: python -m pytest tests/test_send_gate_dubai.py -q
     (or plain `python tests/test_send_gate_dubai.py`)
"""

import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audit import crm_gate, send_cap

DUBAI = timezone(timedelta(hours=4))
# Anchored to a Monday (2026-07-20), not the Sat/Sun 07-18/07-19 pair the
# fixture used before the Sunday send-pause (added 2026-07-26): _AFTERNOON
# rolls to "tomorrow" for a touch-1 opener, and if "tomorrow" lands on a
# Sunday that roll now hits the pause gate first, before any of the
# cutoff/ceiling behavior these tests are actually about. Monday -> Tuesday
# keeps the whole boundary clear of Sunday so these stay pause-agnostic;
# the pause itself gets its own dedicated tests below, anchored on a real
# Saturday -> Sunday roll.
_MORNING = datetime(2026, 7, 20, 9, 0, tzinfo=DUBAI)
_NOON = datetime(2026, 7, 20, 12, 0, tzinfo=DUBAI)
_AFTERNOON = datetime(2026, 7, 20, 15, 0, tzinfo=DUBAI)
_CAP = send_cap.CapState(cap=20, set_on=None, valid=True, inbox="Inbox 1")
_ROW = {"Finding Verified": True, "Email": "a@b.com", "Email Verified": True}

# For the dedicated Sunday-pause tests: a Saturday afternoon (rolls a touch-1
# opener to Sunday) and a plain Sunday moment (for touch 2/3, which never roll
# and so check "today" directly).
_SATURDAY_AFTERNOON = datetime(2026, 7, 18, 15, 0, tzinfo=DUBAI)
_SUNDAY_MORNING = datetime(2026, 7, 19, 9, 0, tzinfo=DUBAI)


def _send(**kw):
    base = dict(row=_ROW, sends_today=0, touch=1, followups_due=0, cap_state=_CAP)
    base.update(kw)
    return crm_gate.check_send(**base)


# --- the send-day boundary -------------------------------------------------

def test_send_day_before_noon_is_today():
    assert send_cap.send_day(_MORNING) == _MORNING.date()
    assert not send_cap.is_after_send_cutoff(_MORNING)


def test_send_day_at_and_after_noon_is_tomorrow():
    tomorrow = _AFTERNOON.date() + timedelta(days=1)
    assert send_cap.send_day(_NOON) == tomorrow      # the cutoff is inclusive
    assert send_cap.send_day(_AFTERNOON) == tomorrow
    assert send_cap.is_after_send_cutoff(_NOON)
    assert send_cap.is_after_send_cutoff(_AFTERNOON)


def test_send_day_accepts_naive_and_utc():
    # A naive datetime is read as Dubai; a UTC one is converted first.
    assert send_cap.send_day(datetime(2026, 7, 18, 9, 0)) == datetime(2026, 7, 18).date()
    utc_afternoon = datetime(2026, 7, 18, 11, 0, tzinfo=timezone.utc)  # 15:00 Dubai
    assert send_cap.send_day(utc_afternoon) == datetime(2026, 7, 19).date()


# --- the Sunday send pause (added 2026-07-26) -------------------------------

def test_touch1_opener_rolling_onto_sunday_is_paused():
    # A Saturday-afternoon opener rolls to Sunday (the cutoff logic above) —
    # the pause must fail it before --sends-next-day/ceiling checks even run.
    ok, problems, _ = _send(
        sends_today=0, followups_due=0, now=_SATURDAY_AFTERNOON, sends_next_day=0,
    )
    assert not ok
    assert "Sunday" in problems[0] and "paused" in problems[0]


def test_touch2_on_sunday_is_paused_regardless_of_headroom():
    # Plenty of headroom, a valid carrier — the pause still fails it first.
    ok, problems, _ = crm_gate.check_send(
        _ROW, sends_today=0, touch=2, carries="leak-fix-offer", cap_state=_CAP,
        now=_SUNDAY_MORNING,
    )
    assert not ok
    assert "Sunday" in problems[0] and "paused" in problems[0]


def test_touch1_opener_rolling_onto_monday_is_not_paused():
    # Sanity check on the other side: Sunday afternoon rolls a fresh opener to
    # Monday, which is not paused.
    sunday_afternoon = _SUNDAY_MORNING.replace(hour=15)
    ok, problems, notes = _send(
        sends_today=18, followups_due=1, now=sunday_afternoon, sends_next_day=0,
    )
    assert ok, problems
    assert "2026-07-20" in notes[0]


# --- touch 1 opener, before noon (unchanged behavior) ----------------------

def test_touch1_before_noon_uses_today_count():
    ok, problems, notes = _send(sends_today=18, followups_due=1, now=_MORNING)
    assert ok, problems
    assert "today" in notes[0]
    assert "opener headroom 1" in notes[0]


def test_touch1_before_noon_rolls_when_today_full():
    ok, problems, _ = _send(sends_today=20, followups_due=0, now=_MORNING)
    assert not ok
    assert "rolls to the next send-day" in problems[0]


# --- touch 1 opener, after noon (attributed to tomorrow) -------------------

def test_touch1_after_noon_requires_sends_next_day():
    ok, problems, _ = _send(sends_today=0, followups_due=0, now=_AFTERNOON)
    assert not ok
    assert "--sends-next-day" in problems[0]


def test_touch1_after_noon_ignores_full_today_uses_tomorrow():
    # Today is completely full, but the opener is scheduled for tomorrow, which
    # is nearly empty — so it passes against tomorrow's ceiling.
    ok, problems, notes = _send(sends_today=20, followups_due=0, now=_AFTERNOON, sends_next_day=2)
    assert ok, problems
    assert "2026-07-21" in notes[0] and "tomorrow" in notes[0]


def test_touch1_after_noon_rolls_when_tomorrow_full():
    ok, problems, _ = _send(sends_today=0, followups_due=1, now=_AFTERNOON, sends_next_day=19)
    assert not ok
    assert "2026-07-21" in problems[0]
    assert "rolls to the next send-day" in problems[0]


# --- follow-ups (touch 2/3) are never rolled -------------------------------

def test_touch2_after_noon_still_counts_today():
    # A follow-up goes out today regardless of the hour: it is gated against
    # today's sends_today, never tomorrow, and never asks for --sends-next-day.
    ok, problems, notes = crm_gate.check_send(
        _ROW, sends_today=5, touch=2, carries="loom-offer", cap_state=_CAP, now=_AFTERNOON,
    )
    assert ok, problems
    assert "sends today 5" in notes[0]

    ok, problems, _ = crm_gate.check_send(
        _ROW, sends_today=20, touch=2, carries="loom-offer", cap_state=_CAP, now=_AFTERNOON,
    )
    assert not ok
    assert "ceiling reached" in problems[0]


# --- carrier renames: call-ask canonical; loom-offer and leak-fix-offer are
# both deprecated aliases. The turn-two artifact has changed twice — a free
# Loom (retired 07-24), the paid Leak Fix (retired 07-27 with The First Five),
# and now a call ask with two specific times. Old labels keep passing so
# in-flight rows and historical logs don't break.

def test_normalize_carrier_maps_both_deprecated_aliases():
    for old in ("loom-offer", "leak-fix-offer"):
        canonical, note = crm_gate.normalize_carrier(old)
        assert canonical == "call-ask", old
        assert note is not None and "DEPRECATED" in note, old

    assert crm_gate.normalize_carrier("second-finding") == ("second-finding", None)
    assert crm_gate.normalize_carrier("bogus")[0] == "bogus"


def test_retired_offer_aliases_still_pass_with_a_deprecation_note():
    # Live rows and queued follow-ups still declare the old labels; they must
    # not start failing, but the caller gets told to move on.
    for old in ("loom-offer", "leak-fix-offer"):
        ok, problems, notes = crm_gate.check_send(
            _ROW, sends_today=5, touch=2, carries=old, cap_state=_CAP, now=_AFTERNOON,
        )
        assert ok, (old, problems)
        assert "carries call-ask" in notes[0], (old, notes)
        assert any("DEPRECATED carrier label" in n for n in notes), (old, notes)


def test_call_ask_is_canonical_and_note_free():
    ok, problems, notes = crm_gate.check_send(
        _ROW, sends_today=5, touch=2, carries="call-ask", cap_state=_CAP,
        now=_AFTERNOON,
    )
    assert ok, problems
    assert "carries call-ask" in notes[0]
    assert not any("DEPRECATED" in n for n in notes), notes


def test_unknown_carrier_fails_listing_canonical_names_only():
    ok, problems, _ = crm_gate.check_send(
        _ROW, sends_today=5, touch=2, carries="bare-bump", cap_state=_CAP, now=_AFTERNOON,
    )
    assert not ok
    joined = " ".join(problems)
    assert "call-ask" in joined
    assert "loom-offer" not in joined
    assert "leak-fix-offer" not in joined


# --- no-pytest fallback ----------------------------------------------------

if __name__ == "__main__":
    import traceback
    passed = failed = 0
    for name, fn in sorted(globals().items()):
        if not (name.startswith("test_") and callable(fn)):
            continue
        try:
            fn()
            passed += 1
        except Exception:
            failed += 1
            print(f"FAIL {name}")
            traceback.print_exc()
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
