"""Tests for the touch-log grammar/parser (audit/touchlog.py, added 2026-07-27
for the lossless Notion -> Airtable migration — docs/uae-track/log-grammar.md).

What is asserted here:

  1. Round trip: render_touch/render_offer/render_source -> parse_body
     recovers the exact same fields, including quoted values with embedded
     `=`/`"`, and a body containing a triple-backtick block (survives the
     four-backtick fence).
  2. Legacy-format parsing against real docs/leads/<slug>/raw.md archives —
     tolerant of the pre-2026-07-27 `[date] — Touch #N — Subject: "..." —
     Sent` shape, reports format="legacy".
  3. Every ERROR condition in validate() fires, and fails closed (non-empty,
     level == "ERROR").
  4. Autoresponders/bounces are excluded from a reply-type requirement and
     from the out-touch numbering, but still show up in the parsed archive
     (never silently dropped).
  5. Touch # mismatch is detected whether the log is missing a block or has
     an extra one past the claimed count.
  6. render_* fails closed (raises, prints nothing) on a half-valid block —
     never emits something that "looks logged" but isn't.

Run: python tests/test_touchlog.py
     (or python -m pytest tests/test_touchlog.py -q)
"""

import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audit import touchlog as tl

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------------------
# Round trip
# ---------------------------------------------------------------------------

def test_round_trip_touch_out_second_finding():
    line = tl.render_touch(
        n=2, dir="out", date="2026-07-28", inbox="Inbox 1", seq="cold",
        carries="second-finding", finding=3, subject="Quick thing on your checkout page",
        thread="18f2a9c4b7e1", gate="PASS", body="Hey Lead\nBody here.",
    )
    parsed = tl.parse_body(line)
    assert len(parsed["touches"]) == 1
    t = parsed["touches"][0]
    assert t["n"] == 2
    assert t["dir"] == "out"
    assert t["date"] == "2026-07-28"
    assert t["inbox"] == "Inbox 1"
    assert t["seq"] == "cold"
    assert t["carries"] == "second-finding"
    assert t["finding"] == 3
    assert t["subject"] == "Quick thing on your checkout page"
    assert t["thread"] == "18f2a9c4b7e1"
    assert t["gate"] == "PASS"
    assert t["body"] == "Hey Lead\nBody here."
    assert t["format"] == "v2"
    assert t["bounce"] is False
    assert t["auto"] is False


def test_round_trip_touch_in_reply():
    line = tl.render_touch(
        n=2, dir="in", date="2026-07-30", reply_to=2, type="price question",
        thread="18f2a9c4b7e1", body="What does this cost?",
    )
    parsed = tl.parse_body(line)
    t = parsed["touches"][0]
    assert t["dir"] == "in"
    assert t["reply_to"] == 2
    assert t["type"] == "price question"
    assert t["body"] == "What does this cost?"


def test_round_trip_embedded_equals_and_quote_in_value():
    subject = 'A "quoted" subject with an = sign'
    line = tl.render_touch(
        n=1, dir="out", date="2026-07-20", inbox="Inbox 1", seq="cold",
        subject=subject, thread="t1", gate="PASS", body="hi",
    )
    parsed = tl.parse_body(line)
    assert parsed["touches"][0]["subject"] == subject


def test_round_trip_body_with_triple_backtick_survives_four_backtick_fence():
    body = "Here is code:\n```\nprint('hi')\n```\nEnd."
    line = tl.render_touch(
        n=1, dir="out", date="2026-07-20", inbox="Inbox 1", seq="cold",
        subject="x", thread="t1", gate="PASS", body=body,
    )
    parsed = tl.parse_body(line)
    assert parsed["touches"][0]["body"] == body


def test_round_trip_offer():
    line = tl.render_offer(
        type="Sprint", amount=2575, currency="AED", date="2026-08-02",
        status="Declined", rung=0, objection="price", terms="pay after",
    )
    parsed = tl.parse_body(line)
    o = parsed["offers"][0]
    assert o["type"] == "Sprint"
    assert o["amount"] == 2575
    assert o["currency"] == "AED"
    assert o["date"] == "2026-08-02"
    assert o["status"] == "Declined"
    assert o["objection"] == "price"
    assert o["terms"] == "pay after"


def test_round_trip_source():
    line = tl.render_source(
        channel="Google Footprint", query="Dubai business coach kajabi", date="2026-07-27",
    )
    parsed = tl.parse_body(line)
    assert parsed["source"] == {
        "channel": "Google Footprint", "query": "Dubai business coach kajabi", "date": "2026-07-27",
    }


def test_round_trip_multiple_records_in_one_body():
    text = "\n".join([
        tl.render_source(channel="LinkedIn", query="dubai life coach", date="2026-07-10"),
        tl.render_touch(n=1, dir="out", date="2026-07-11", inbox="Inbox 1", seq="cold",
                        carries="opener", subject="x", thread="t1", gate="PASS", body="hi"),
        tl.render_touch(n=1, dir="in", date="2026-07-12", reply_to=1, type="Interested",
                        thread="t1", body="tell me more"),
        tl.render_offer(type="Leak Fix", amount=500, currency="AED", date="2026-07-13",
                        status="Proposed", rung=0),
    ])
    parsed = tl.parse_body(text)
    assert len(parsed["touches"]) == 2
    assert len(parsed["offers"]) == 1
    assert parsed["source"]["channel"] == "LinkedIn"
    assert parsed["warnings"] == []


# ---------------------------------------------------------------------------
# Legacy parsing against real archives
# ---------------------------------------------------------------------------

def _raw(slug):
    with open(os.path.join(REPO_ROOT, "docs", "leads", slug, "raw.md")) as f:
        return f.read()


def test_legacy_parses_adam_ashcroft():
    parsed = tl.parse_body(_raw("adam-ashcroft"))
    assert len(parsed["touches"]) == 1
    t = parsed["touches"][0]
    assert t["format"] == "legacy"
    assert t["n"] == 1
    assert t["dir"] == "out"
    assert t["subject"] == "no. 2 in dubai non-fiction"
    assert t["body"] and t["body"].startswith("Hey Adam")


def test_legacy_parses_sadia_khan():
    parsed = tl.parse_body(_raw("sadia-khan"))
    assert len(parsed["touches"]) == 1
    assert parsed["touches"][0]["n"] == 2
    assert parsed["touches"][0]["format"] == "legacy"


def test_legacy_parses_avneet_kohli_multi_touch_with_replies():
    parsed = tl.parse_body(_raw("avneet-kohli"))
    out = [t for t in parsed["touches"] if t["dir"] == "out"]
    inn = [t for t in parsed["touches"] if t["dir"] == "in"]
    assert [t["n"] for t in out] == [1, 2, 3, 4, 5, 6]
    assert all(t["format"] == "legacy" for t in out)
    # touch 1's reply was "No reply" — no synthetic inbound record for it.
    assert 1 not in [t["reply_to"] for t in inn]
    # touches 2, 3, 4, 6 got real replies.
    assert set(t["reply_to"] for t in inn) == {2, 3, 4, 6}
    for t in inn:
        assert t["type"] is None  # legacy never captured reply type


# ---------------------------------------------------------------------------
# validate() — ERROR conditions
# ---------------------------------------------------------------------------

def _out_touch(**overrides):
    fields = dict(n=1, dir="out", date="2026-07-20", inbox="Inbox 1", seq="cold",
                  subject="x", thread="t1", gate="PASS", body="hi")
    fields.update(overrides)
    return fields


def test_validate_missing_required_token_is_error():
    # Hand-build a line missing `gate` — render_touch would refuse to emit
    # this, so build it directly to exercise validate()'s own check.
    text = 'TOUCH: n=1 dir=out date=2026-07-20 inbox="Inbox 1" seq=cold subject="x" thread=t1\n````\nhi\n````'
    problems = tl.validate(None, text, today=date(2026, 7, 27))
    assert any(p.level == "ERROR" and "gate is required" in p.message for p in problems)


def test_validate_inbound_missing_type_is_error():
    # render_touch itself refuses to emit this (self-lints before printing) —
    # hand-build the line to exercise validate()'s independent check on a
    # body that reached Notion some other way.
    text = 'TOUCH: n=1 dir=in date=2026-07-20 reply_to=1 thread=t1\n````\nhi\n````'
    problems = tl.validate(None, text, today=date(2026, 7, 27))
    assert any(p.level == "ERROR" and "type=" in p.message for p in problems)


def test_validate_inbound_auto_true_needs_no_type():
    text = tl.render_touch(n=1, dir="in", date="2026-07-20", reply_to=1, thread="t1",
                            auto="true", body="Thanks for your message.")
    problems = tl.validate(None, text, today=date(2026, 7, 27))
    assert not any(p.level == "ERROR" for p in problems)


def test_validate_inbound_bounce_true_needs_no_type():
    text = tl.render_touch(n=1, dir="in", date="2026-07-20", reply_to=1, thread="t1",
                            bounce="true", body="")
    problems = tl.validate(None, text, today=date(2026, 7, 27))
    assert not any(p.level == "ERROR" for p in problems)


def test_validate_n_not_contiguous_from_1():
    text = "\n".join([
        tl.render_touch(**_out_touch(n=1)),
        tl.render_touch(**_out_touch(n=3, carries="leak-fix-offer", date="2026-07-29")),
    ])
    problems = tl.validate(None, text, today=date(2026, 7, 27))
    assert any(p.level == "ERROR" and "missing touch number" in p.message for p in problems)


def test_validate_duplicate_n_in_out_direction():
    text = "\n".join([
        tl.render_touch(**_out_touch(n=1)),
        tl.render_touch(**_out_touch(n=1, date="2026-07-25")),
    ])
    problems = tl.validate(None, text, today=date(2026, 7, 27))
    assert any(p.level == "ERROR" and "duplicate touch number" in p.message for p in problems)


def test_validate_future_date_is_error():
    text = tl.render_touch(**_out_touch(date="2099-01-01"))
    problems = tl.validate(None, text, today=date(2026, 7, 27))
    assert any(p.level == "ERROR" and "in the future" in p.message for p in problems)


def test_validate_inbound_date_before_out_touch_is_error():
    text = "\n".join([
        tl.render_touch(**_out_touch(n=1, date="2026-07-20")),
        tl.render_touch(n=1, dir="in", date="2026-07-15", reply_to=1, type="Blunt",
                        thread="t1", body="no"),
    ])
    problems = tl.validate(None, text, today=date(2026, 7, 27))
    assert any(p.level == "ERROR" and "earlier than the touch it replies to" in p.message
               for p in problems)


def test_validate_second_finding_rank_not_in_bank_is_error():
    text = tl.render_touch(**_out_touch(n=2, carries="second-finding", finding=9))
    row = {"Findings Bank": "1. USED-T1 | SHALLOW | checkout button 404s\n"
                              "2. UNUSED | DEEP | pricing split across platforms"}
    problems = tl.validate(row, text, today=date(2026, 7, 27))
    assert any(p.level == "ERROR" and "not a real rank" in p.message for p in problems)


def test_validate_second_finding_rank_present_in_bank_passes():
    text = "\n".join([
        tl.render_touch(**_out_touch(n=1)),
        tl.render_touch(**_out_touch(n=2, carries="second-finding", finding=2, date="2026-07-23")),
    ])
    row = {"Findings Bank": "1. USED-T1 | SHALLOW | checkout button 404s\n"
                              "2. UNUSED | DEEP | pricing split across platforms",
           "Touch #": 2}
    problems = tl.validate(row, text, today=date(2026, 7, 27))
    assert not any(p.level == "ERROR" for p in problems)


def test_validate_unregistered_inbox_is_error():
    text = tl.render_touch(**_out_touch(inbox="Inbox 99"))
    problems = tl.validate(None, text, today=date(2026, 7, 27))
    assert any(p.level == "ERROR" and "not a registered inbox" in p.message for p in problems)


def test_validate_unterminated_fence_is_error():
    text = 'TOUCH: n=1 dir=out date=2026-07-20 inbox="Inbox 1" seq=cold subject="x" thread=t1 gate=PASS\n````\nhi\n'
    problems = tl.validate(None, text, today=date(2026, 7, 27))
    assert any(p.level == "ERROR" and "unterminated" in p.message for p in problems)


def test_validate_bad_enum_value_is_error():
    text = 'TOUCH: n=1 dir=sideways date=2026-07-20 inbox="Inbox 1" seq=cold subject="x" thread=t1 gate=PASS\n````\nhi\n````'
    problems = tl.validate(None, text, today=date(2026, 7, 27))
    assert any(p.level == "ERROR" and "dir=" in p.message for p in problems)


# --- Touch # reconciliation (both directions) -------------------------------

def test_validate_touch_number_missing_from_log():
    text = tl.render_touch(**_out_touch(n=2, carries="leak-fix-offer", date="2026-07-25"))
    row = {"Touch #": 2}
    problems = tl.validate(row, text, today=date(2026, 7, 27))
    assert any(p.level == "ERROR" and "no block for touch 1" in p.message for p in problems)


def test_validate_touch_number_has_extra_block_past_claimed_count():
    text = "\n".join([
        tl.render_touch(**_out_touch(n=1)),
        tl.render_touch(**_out_touch(n=2, carries="leak-fix-offer", date="2026-07-25")),
    ])
    row = {"Touch #": 1}
    problems = tl.validate(row, text, today=date(2026, 7, 27))
    assert any(p.level == "ERROR" and "Touch # is only 1" in p.message for p in problems)


def test_validate_touch_number_matches_log_passes():
    text = "\n".join([
        tl.render_touch(**_out_touch(n=1)),
        tl.render_touch(**_out_touch(n=2, carries="leak-fix-offer", date="2026-07-25")),
    ])
    row = {"Touch #": 2}
    problems = tl.validate(row, text, today=date(2026, 7, 27))
    assert not any(p.level == "ERROR" for p in problems)


# --- bounce/auto exclusion --------------------------------------------------

def test_bounce_excluded_from_out_numbering_but_not_dropped():
    text = "\n".join([
        tl.render_touch(n=1, dir="out", date="2026-07-19", inbox="Inbox 1", seq="cold",
                        carries="opener", subject="x", thread="t1", gate="PASS",
                        bounce="true", body="attempt"),
        tl.render_touch(**_out_touch(n=1, date="2026-07-20")),
    ])
    parsed = tl.parse_body(text)
    assert len(parsed["touches"]) == 2  # both preserved, never dropped
    row = {"Touch #": 1}
    problems = tl.validate(row, text, today=date(2026, 7, 27))
    assert not any(p.level == "ERROR" for p in problems)


def test_auto_excluded_from_reply_denominator():
    # An autoresponder never requires `type` and should not trip the
    # "Last Reply Type disagrees" WARN either.
    text = "\n".join([
        tl.render_touch(**_out_touch(n=1)),
        tl.render_touch(n=1, dir="in", date="2026-07-21", reply_to=1, thread="t1",
                        auto="true", body="Thanks for reaching out, I'll be back on Monday."),
    ])
    row = {"Touch #": 1, "Last Reply Type": "Interested"}
    problems = tl.validate(row, text, today=date(2026, 7, 27))
    assert not any("disagrees" in p.message for p in problems)


# ---------------------------------------------------------------------------
# WARN conditions
# ---------------------------------------------------------------------------

def test_warn_empty_body_on_non_bounce_touch():
    text = 'TOUCH: n=1 dir=out date=2026-07-20 inbox="Inbox 1" seq=cold subject="x" thread=t1 gate=PASS'
    problems = tl.validate(None, text, today=date(2026, 7, 27))
    assert any(p.level == "WARN" and "empty body" in p.message for p in problems)


def test_warn_unknown_token_key_preserved_not_dropped():
    text = ('TOUCH: n=1 dir=out date=2026-07-20 inbox="Inbox 1" seq=cold subject="x" '
            'thread=t1 gate=PASS mystery=1\n````\nhi\n````')
    parsed = tl.parse_body(text)
    assert parsed["touches"][0]["mystery"] == "1"  # preserved
    problems = tl.validate(None, text, today=date(2026, 7, 27))
    assert any(p.level == "WARN" and "unknown token key" in p.message for p in problems)


def test_warn_last_reply_type_disagrees_with_logged_type():
    text = "\n".join([
        tl.render_touch(**_out_touch(n=1)),
        tl.render_touch(n=1, dir="in", date="2026-07-21", reply_to=1, type="Blunt",
                        thread="t1", body="no thanks"),
    ])
    row = {"Touch #": 1, "Last Reply Type": "Interested"}
    problems = tl.validate(row, text, today=date(2026, 7, 27))
    assert any(p.level == "WARN" and "disagrees" in p.message for p in problems)


def test_warn_offer_status_transition_without_prior_proposed():
    text = tl.render_offer(type="Sprint", amount=2575, currency="AED", date="2026-08-05",
                           status="Declined")
    problems = tl.validate(None, text, today=date(2026, 7, 27))
    assert any(p.level == "WARN" and "no earlier Proposed line" in p.message for p in problems)


def test_no_warn_offer_status_transition_with_prior_proposed():
    text = "\n".join([
        tl.render_offer(type="Sprint", amount=2575, currency="AED", date="2026-08-02", status="Proposed"),
        tl.render_offer(type="Sprint", amount=2575, currency="AED", date="2026-08-05", status="Declined"),
    ])
    problems = tl.validate(None, text, today=date(2026, 7, 27))
    assert not any("no earlier Proposed line" in p.message for p in problems)


# ---------------------------------------------------------------------------
# render_* fails closed
# ---------------------------------------------------------------------------

def test_render_touch_raises_on_missing_required_field():
    try:
        tl.render_touch(n=1, dir="out", date="2026-07-20", thread="t1", body="hi")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "inbox is required" in str(exc)


def test_render_touch_raises_on_bad_carrier():
    try:
        tl.render_touch(n=2, dir="out", date="2026-07-20", inbox="Inbox 1", seq="cold",
                        subject="x", thread="t1", gate="PASS", carries="bogus", body="hi")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "carries=" in str(exc)


def test_render_offer_raises_on_bad_type():
    try:
        tl.render_offer(type="Bogus", amount=100, currency="AED", date="2026-07-20", status="Proposed")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "type=" in str(exc)


def test_render_source_raises_on_missing_query():
    try:
        tl.render_source(channel="LinkedIn", date="2026-07-20")
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "query" in str(exc)


def test_render_touch_deprecated_carrier_still_renders():
    line = tl.render_touch(n=2, dir="out", date="2026-07-20", inbox="Inbox 1", seq="cold",
                           subject="x", thread="t1", gate="PASS", carries="loom-offer", body="hi")
    parsed = tl.parse_body(line)
    assert parsed["touches"][0]["carries"] == "leak-fix-offer"  # normalized to canonical


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
            except Exception as e:  # noqa: BLE001
                failed += 1
                print(f"ERROR {name}: {type(e).__name__}: {e}")
    print(f"{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
