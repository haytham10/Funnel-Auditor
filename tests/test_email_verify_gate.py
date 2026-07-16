"""Tests for the deliverability layer added 2026-07-16:

  1. email_check.classify_verification — MillionVerifier result → PASS/WARN/FAIL,
     failing SAFE (never PASS on an ambiguous or missing result).
  2. crm_gate.check_send — now requires `Email Verified` checked, closing the
     old `"@" in email` hole that let two bounce-prone addresses through.

Run: python -m pytest tests/test_email_verify_gate.py -q
     (or plain `python tests/test_email_verify_gate.py` for the no-pytest path)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audit import email_check
from audit.crm_gate import check_send


# --- classify_verification -------------------------------------------------

def test_verify_ok_is_pass():
    v, _ = email_check.classify_verification({"email": "a@b.com", "result": "ok"})
    assert v == "PASS"


def test_verify_valid_alias_is_pass():
    v, _ = email_check.classify_verification({"result": "valid"})
    assert v == "PASS"


def test_verify_invalid_is_fail():
    # The Adil/Chiara hard-bounce case: mailbox does not exist.
    v, d = email_check.classify_verification({"result": "invalid"})
    assert v == "FAIL"
    assert "never send" in d[0]


def test_verify_disposable_is_fail():
    v, _ = email_check.classify_verification({"result": "disposable"})
    assert v == "FAIL"


def test_verify_catch_all_is_warn_not_pass():
    # Domain accepts everything — real bounce risk, must NOT auto-check the box.
    v, _ = email_check.classify_verification({"result": "catch_all"})
    assert v == "WARN"


def test_verify_unknown_is_warn():
    v, _ = email_check.classify_verification({"result": "unknown"})
    assert v == "WARN"


def test_verify_missing_result_is_warn_fails_safe():
    assert email_check.classify_verification(None)[0] == "WARN"
    assert email_check.classify_verification({})[0] == "WARN"
    assert email_check.classify_verification({"email": "a@b.com"})[0] == "WARN"


def test_verify_unrecognized_token_never_passes():
    # A token we don't know about must never be promoted to PASS.
    v, _ = email_check.classify_verification({"result": "banana"})
    assert v == "WARN"


def test_verify_reads_status_when_result_absent():
    v, _ = email_check.classify_verification({"status": "ok"})
    assert v == "PASS"


def test_print_verify_exit_codes():
    assert email_check.print_verify("a@b.com", {"result": "ok"}) == 0
    assert email_check.print_verify("a@b.com", {"result": "catch_all"}) == 0  # WARN
    assert email_check.print_verify("a@b.com", {"result": "invalid"}) == 1    # FAIL


# --- crm_gate send: Email Verified enforcement -----------------------------

def _sendable_row(**over):
    """A row that would PASS the send gate if Email Verified is set."""
    row = {
        "Contact Name": "Jane Coach",
        "Finding Verified": "__YES__",
        "Email": "jane@janedoe.com",
        "Email Verified": "__YES__",
    }
    row.update(over)
    return row


def test_send_blocks_when_email_verified_unchecked():
    ok, problems, _ = check_send(_sendable_row(**{"Email Verified": "__NO__"}),
                                 sends_today=0, touch=1, followups_due=0)
    assert not ok
    assert any("Email Verified is unchecked" in p for p in problems)


def test_send_blocks_when_email_verified_missing_fails_closed():
    row = _sendable_row()
    del row["Email Verified"]
    ok, problems, _ = check_send(row, sends_today=0, touch=1, followups_due=0)
    assert not ok
    assert any("Email Verified is unchecked" in p for p in problems)


def test_send_passes_with_verified_email_and_headroom():
    ok, problems, _ = check_send(_sendable_row(),
                                 sends_today=0, touch=1, followups_due=0)
    assert ok, problems


def test_send_still_requires_finding_verified():
    ok, problems, _ = check_send(_sendable_row(**{"Finding Verified": "__NO__"}),
                                 sends_today=0, touch=1, followups_due=0)
    assert not ok
    assert any("Finding Verified" in p for p in problems)


def test_send_no_address_reports_address_not_verified_flag():
    # With no '@', the address problem fires (not the verified-flag one) —
    # they shouldn't double-report on the same missing field.
    ok, problems, _ = check_send(_sendable_row(**{"Email": "", "Email Verified": "__NO__"}),
                                 sends_today=0, touch=1, followups_due=0)
    assert not ok
    assert any("no usable address" in p for p in problems)
    assert not any("Email Verified is unchecked" in p for p in problems)


def test_send_accepts_plain_yes_shape():
    # Notion checkboxes can arrive as bool true or "Yes" as well as "__YES__".
    ok, _, _ = check_send(_sendable_row(**{"Email Verified": True}),
                          sends_today=0, touch=1, followups_due=0)
    assert ok
    ok2, _, _ = check_send(_sendable_row(**{"Email Verified": "Yes"}),
                           sends_today=0, touch=1, followups_due=0)
    assert ok2


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"ok   {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
