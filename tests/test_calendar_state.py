"""
Tests for audit/calendar_state.py — the acquisition-state calendar check.

Run: python tests/test_calendar_state.py

Every test stubs `requests.get`; nothing here touches the network or any real
coach's calendar.

The load-bearing test in this file is
`test_external_calendar_error_raises_never_reports_empty`. During design, a
live Calendly call returned HTTP 400 with
`{"failure": {"code": "external_calendar_error"}}` and no `days` key, and a
parser doing `.get("days", [])` read that as "this coach has no availability."
That is a fabricated finding, which is the one thing this repo forbids
outright. If that test ever goes green by returning zero instead of raising,
the check is broken no matter what else passes.
"""

import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audit import calendar_state as cs  # noqa: E402

_TODAY = date(2026, 7, 27)  # a Monday, so weekday math is stable


class _FakeResponse:
    def __init__(self, payload, ok=True, status_code=200, text=None):
        self._payload = payload
        self.ok = ok
        self.status_code = status_code
        self.text = text if text is not None else "{}"

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


def _day(d, spots=3, status="available"):
    return {"date": d, "status": status,
            "spots": [{"status": "available", "start_time": f"{d}T{9 + i}:00:00+04:00"}
                      for i in range(spots)]}


def _calendly_stub(range_payload):
    """URL-dispatching stub for Calendly's three-hop chain."""
    def fake_get(url, *a, **k):
        if "/profiles/" in url and "/event_types" in url:
            return _FakeResponse([{"name": "Discovery Call", "slug": "discovery",
                                   "uuid": "abc-123"}])
        if "/profiles/" in url:
            return _FakeResponse({"name": "Sadia Khan"})
        if "/calendar/range" in url:
            return range_payload
        raise AssertionError(f"unexpected URL {url}")
    return fake_get


# --- platform routing -----------------------------------------------------

def test_platform_for_recognises_known_schedulers(mp):
    assert cs.platform_for("https://calendly.com/therapybysadia/call") == "calendly.com"
    assert cs.platform_for("https://cal.com/peer") == "cal.com"
    assert cs.platform_for("https://example.com/book") == ""


def test_unsupported_scheduler_raises_rather_than_guessing(mp):
    # TidyCal's real routes were never resolved. Returning "no availability"
    # for it would be a guess dressed as a finding.
    try:
        cs.check("https://tidycal.com/someone/call", today=_TODAY)
    except cs.CalendarStateError as e:
        assert "no verified public availability endpoint" in str(e), e
    else:
        raise AssertionError("expected CalendarStateError for tidycal")


def test_non_booking_url_raises(mp):
    try:
        cs.check("https://somecoach.com/contact", today=_TODAY)
    except cs.CalendarStateError as e:
        assert "not a supported booking page" in str(e)
    else:
        raise AssertionError("expected CalendarStateError")


# --- THE trap -------------------------------------------------------------

def test_external_calendar_error_raises_never_reports_empty(mp):
    """A 400 + failure.external_calendar_error must RAISE.

    Reproduced live on 2026-07-27. If this ever returns a result with
    open_slots == 0, the check is fabricating findings.
    """
    err = _FakeResponse(
        {"failure": {"code": "external_calendar_error",
                     "error": "this calendar is currently unavailable"}},
        ok=False, status_code=400,
    )
    mp.setattr(cs.requests, "get", _calendly_stub(err))
    try:
        result = cs.check("https://calendly.com/x/discovery", today=_TODAY, reads=1)
    except cs.CalendarStateError as e:
        assert "external_calendar_error" in str(e)
        assert "NOT an empty calendar" in str(e)
    else:
        raise AssertionError(
            f"fabricated a finding instead of raising: {result}"
        )


def test_range_too_wide_is_refused_before_any_request(mp):
    def explode(*a, **k):
        raise AssertionError("should not have made a request")
    mp.setattr(cs.requests, "get", explode)
    try:
        cs.check("https://calendly.com/x/y", window_days=65, today=_TODAY)
    except cs.CalendarStateError as e:
        assert "exceeds" in str(e)
    else:
        raise AssertionError("expected CalendarStateError")


def test_missing_days_key_raises_rather_than_defaulting(mp):
    # No `failure`, 200, but no `days` either — an unexpected shape. Guessing
    # zero here is the same bug wearing different clothes.
    mp.setattr(cs.requests, "get", _calendly_stub(_FakeResponse({"today": "2026-07-27"})))
    try:
        cs.check("https://calendly.com/x/discovery", today=_TODAY, reads=1)
    except cs.CalendarStateError as e:
        assert "refusing to guess" in str(e)
    else:
        raise AssertionError("expected CalendarStateError")


def test_non_json_body_raises(mp):
    bad = _FakeResponse(ValueError("no json"), ok=False, status_code=502, text="<html>502</html>")
    mp.setattr(cs.requests, "get", _calendly_stub(bad))
    try:
        cs.check("https://calendly.com/x/discovery", today=_TODAY, reads=1)
    except cs.CalendarStateError as e:
        assert "non-JSON" in str(e)
    else:
        raise AssertionError("expected CalendarStateError")


def test_network_error_raises(mp):
    def boom(*a, **k):
        raise cs.requests.RequestException("connection reset")
    mp.setattr(cs.requests, "get", boom)
    try:
        cs.check("https://calendly.com/x/discovery", today=_TODAY, reads=1)
    except cs.CalendarStateError as e:
        assert "network error" in str(e)
    else:
        raise AssertionError("expected CalendarStateError")


# --- the three verdicts ---------------------------------------------------

def test_wide_open_is_deep_and_opener_legal(mp):
    # 20 of 22 weekdays bookable — the Sadia Khan shape (271 slots live).
    days = [_day(f"2026-07-{d:02d}", spots=10) for d in range(28, 32)]
    days += [_day(f"2026-08-{d:02d}", spots=10) for d in range(1, 21)]
    mp.setattr(cs.requests, "get", _calendly_stub(_FakeResponse({"days": days})))
    r = cs.check("https://calendly.com/therapybysadia/discovery", today=_TODAY, reads=2)
    assert r["verdict"] == "wide_open", r
    assert r["depth"] == "DEEP"
    assert r["opener_legal"] is True
    assert r["open_slots"] == 240, r["open_slots"]
    assert r["reads"] == 2


def test_none_published_is_shallow_not_an_opener(mp):
    """Zero bookable time is a CONFIG BUG she fixes herself.

    This is the walk.md:44-46 split: an empty calendar widget is shallow, a
    working calendar nobody books is deep. Getting this backwards ships an
    opener the lead closes in five minutes and walks away from.
    """
    mp.setattr(cs.requests, "get", _calendly_stub(_FakeResponse({"days": []})))
    r = cs.check("https://calendly.com/x/discovery", today=_TODAY, reads=1)
    assert r["verdict"] == "none_published", r
    assert r["depth"] == "SHALLOW"
    assert r["opener_legal"] is False
    assert "fix herself" in r["detail"]


def test_partial_is_neither(mp):
    days = [_day("2026-07-29", spots=2), _day("2026-08-04", spots=2)]
    mp.setattr(cs.requests, "get", _calendly_stub(_FakeResponse({"days": days})))
    r = cs.check("https://calendly.com/x/discovery", today=_TODAY, reads=1)
    assert r["verdict"] == "partial", r
    assert r["opener_legal"] is False
    # A normally-busy calendar is not a shallow finding, it is NOT A FINDING.
    # Tagging it SHALLOW would invite banking it as touch-2 material.
    assert r["depth"] is None, r
    assert r["bankable"] is False, r


def test_days_omits_unavailable_so_length_is_not_window_width(mp):
    # Calendly drops unavailable days entirely; a non-available entry that
    # does slip through must still not be counted.
    days = [_day("2026-07-29", spots=2), _day("2026-07-30", spots=0, status="unavailable")]
    mp.setattr(cs.requests, "get", _calendly_stub(_FakeResponse({"days": days})))
    r = cs.check("https://calendly.com/x/discovery", today=_TODAY, reads=1)
    assert r["available_days"] == 1, r
    assert r["open_slots"] == 2, r


# --- consistency ----------------------------------------------------------

def test_disagreeing_reads_refuse_to_bank_a_verdict(mp):
    """One read is not evidence — the live 400 cleared on 4 of 4 retries."""
    payloads = [
        _FakeResponse({"days": []}),
        _FakeResponse({"days": [_day(f"2026-08-{d:02d}", spots=8) for d in range(1, 21)]}),
    ]
    calls = {"n": 0}

    def fake_get(url, *a, **k):
        if "/calendar/range" in url:
            p = payloads[min(calls["n"], len(payloads) - 1)]
            calls["n"] += 1
            return p
        return _calendly_stub(None)(url, *a, **k)

    mp.setattr(cs.requests, "get", fake_get)
    try:
        cs.check("https://calendly.com/x/discovery", today=_TODAY, reads=2)
    except cs.CalendarStateError as e:
        assert "disagreed" in str(e)
    else:
        raise AssertionError("expected CalendarStateError on disagreeing reads")


def test_unknown_event_slug_lists_what_exists(mp):
    mp.setattr(cs.requests, "get", _calendly_stub(_FakeResponse({"days": []})))
    try:
        cs.check("https://calendly.com/x/no-such-event", today=_TODAY, reads=1)
    except cs.CalendarStateError as e:
        assert "not found" in str(e) and "discovery" in str(e)
    else:
        raise AssertionError("expected CalendarStateError")


# --- cal.com --------------------------------------------------------------

def test_calcom_reads_slots_by_numeric_event_type_id(mp):
    def fake_get(url, *a, **k):
        if url.startswith("https://cal.com/"):
            return _FakeResponse({}, text='window.__DATA__={"eventTypeId":127};')
        if "/v2/slots" in url:
            return _FakeResponse({"data": {
                "2026-08-03": [{"start": "..."}, {"start": "..."}],
                "2026-08-04": [{"start": "..."}],
                "2026-08-05": [],
            }})
        raise AssertionError(f"unexpected URL {url}")

    mp.setattr(cs.requests, "get", fake_get)
    r = cs.check("https://cal.com/peer", today=_TODAY, reads=1)
    assert r["platform"] == "cal.com"
    assert r["available_days"] == 2, r
    assert r["open_slots"] == 3, r


def test_calcom_without_event_type_id_raises(mp):
    def fake_get(url, *a, **k):
        return _FakeResponse({}, text="<html>nothing useful</html>")
    mp.setattr(cs.requests, "get", fake_get)
    try:
        cs.check("https://cal.com/peer", today=_TODAY, reads=1)
    except cs.CalendarStateError as e:
        assert "no eventTypeId" in str(e)
    else:
        raise AssertionError("expected CalendarStateError")


if __name__ == "__main__":
    class _MonkeyPatch:
        def __init__(self):
            self._undo = []

        def setattr(self, obj, name, value):
            self._undo.append((obj, name, getattr(obj, name)))
            setattr(obj, name, value)

        def undo(self):
            for obj, name, old in reversed(self._undo):
                setattr(obj, name, old)

    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        mp = _MonkeyPatch()
        try:
            fn(mp)
            print(f"ok   {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
        finally:
            mp.undo()
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
