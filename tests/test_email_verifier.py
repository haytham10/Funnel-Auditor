"""Tests for the ZeroBounce email verifier (audit/email_verifier.py), the
default replacement for `apify.verify_emails` added 2026-07-17 to keep
verification off Apify's small monthly cap.

Only `_normalize` is network-free and worth unit testing directly — it's
the seam that makes ZeroBounce's response shape readable by the existing
`email_check.classify_verification` (which expects email/status/free/role).
`verify_emails` itself (the network call) is exercised end-to-end only via
the CLI's fail-closed path (missing key -> EmailVerifierError), covered by
`test_verify_emails_fails_closed_without_key` below.

Run: python -m pytest tests/test_email_verifier.py -q
     (or plain `python tests/test_email_verifier.py` for the no-pytest path)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audit import email_check, email_verifier


# --- _normalize --------------------------------------------------------------

def test_normalize_valid_maps_to_email_check_pass():
    row = {"address": "jane@janedoe.com", "status": "valid", "sub_status": "",
          "free_email": False}
    norm = email_verifier._normalize(row)
    assert norm["email"] == "jane@janedoe.com"
    verdict, _ = email_check.classify_verification(norm)
    assert verdict == "PASS"


def test_normalize_hyphenated_catch_all_is_warn_not_pass():
    # ZeroBounce spells it "catch-all" (hyphen), unlike MillionVerifier's
    # "catch_all" — the whole reason email_check.py grew a hyphenated entry.
    row = {"address": "info@site.com", "status": "catch-all", "sub_status": ""}
    norm = email_verifier._normalize(row)
    verdict, _ = email_check.classify_verification(norm)
    assert verdict == "WARN"


def test_normalize_do_not_mail_is_fail():
    row = {"address": "spam@site.com", "status": "do_not_mail", "sub_status": "role_based"}
    norm = email_verifier._normalize(row)
    verdict, _ = email_check.classify_verification(norm)
    assert verdict == "FAIL"


def test_normalize_role_based_flagged_from_sub_status():
    row = {"address": "info@site.com", "status": "valid", "sub_status": "role_based",
          "free_email": False}
    norm = email_verifier._normalize(row)
    assert norm["role"] is True


def test_normalize_free_email_flag_passed_through():
    row = {"address": "jane@gmail.com", "status": "valid", "free_email": True}
    norm = email_verifier._normalize(row)
    assert norm["free"] is True


def test_normalize_missing_sub_status_does_not_crash():
    norm = email_verifier._normalize({"address": "a@b.com", "status": "invalid"})
    assert norm["role"] is False


# --- fail-closed without a key ------------------------------------------------

def test_verify_emails_fails_closed_without_key():
    os.environ.pop("ZEROBOUNCE_API_KEY", None)
    try:
        email_verifier.verify_emails(["a@b.com"])
    except email_verifier.EmailVerifierError as e:
        assert "ZEROBOUNCE_API_KEY" in str(e)
    else:
        raise AssertionError("expected EmailVerifierError with no key set")


def test_verify_emails_requires_at_least_one_address():
    os.environ["ZEROBOUNCE_API_KEY"] = "test-key-not-real"
    try:
        try:
            email_verifier.verify_emails([])
        except email_verifier.EmailVerifierError as e:
            assert "at least one address" in str(e)
        else:
            raise AssertionError("expected EmailVerifierError for empty list")
    finally:
        del os.environ["ZEROBOUNCE_API_KEY"]


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
