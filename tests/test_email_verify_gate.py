"""email_check.classify_verification: a verifier result -> PASS / WARN / FAIL.

Fails SAFE. An ambiguous or missing result is never a PASS, because the cost
of a wrong PASS is a real bounce against a sending domain and the cost of a
wrong WARN is one address looked at by hand.

The send-gate half of this file left with crm_gate when sending moved to
Smartlead. What remains is the classifier, which is provider-agnostic and
still the thing standing between a scraped string and an upload file.

Run: python -m pytest tests/test_email_verify_gate.py -q
     (or plain `python tests/test_email_verify_gate.py`)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audit import email_check



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


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  ok    {name}")
            except AssertionError as exc:
                failures += 1
                print(f"  FAIL  {name}: {exc}")
    print(f"\n{failures} failure(s)")
    sys.exit(1 if failures else 0)
