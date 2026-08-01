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


def test_local_mx_is_warn_and_says_no_verifier_ran():
    # The local check can prove a domain takes mail, never that a mailbox
    # exists. It must never be able to clear an address on its own.
    v, d = email_check.classify_verification({"result": "local_mx"})
    assert v == "WARN"
    assert "mailbox unconfirmed" in d[0]


def test_no_result_is_warn_and_names_the_short_run():
    v, d = email_check.classify_verification({"result": "no_result"})
    assert v == "WARN"
    assert "came back short" in d[0]


def test_print_verify_names_who_answered(capsys):
    # Two WARNs that read alike but came from a paid verifier and from the
    # local check are not the same fact.
    email_check.print_verify("a@b.com", {"result": "catch_all", "verified_by": "apify"})
    assert "[via apify]" in capsys.readouterr().out
    email_check.print_verify("a@b.com", {"result": "local_mx", "verified_by": "local"})
    assert "[via local]" in capsys.readouterr().out
    email_check.print_verify("a@b.com", None)
    assert "[via none]" in capsys.readouterr().out


# --- batch_health: an outage is a property of the run, not of an address ----


def _rows(*tokens):
    return [{"email": f"a{i}@b.com", "result": t} for i, t in enumerate(tokens)]


def test_batch_health_is_quiet_on_a_mixed_run():
    assert email_check.batch_health(
        _rows("ok", "catch_all", "invalid", "ok", "unknown", "ok")) is None


def test_batch_health_is_quiet_below_the_minimum():
    # Four inconclusives in a row is a Tuesday. Forty is an outage, and the
    # rule has to be able to tell them apart without crying wolf.
    assert email_check.batch_health(_rows("error", "error", "error", "error")) is None


def test_batch_health_flags_a_run_with_nothing_conclusive():
    line = email_check.batch_health(_rows(*(["catch_all"] * 8)))
    assert line is not None
    assert "SUSPECT" in line and "8/8 inconclusive" in line


def test_batch_health_flags_the_real_outage_shape():
    # What account56 actually did: every address, valid or not, came back an
    # actor-side error, and it read as a run of catch-all domains.
    line = email_check.batch_health(_rows(*(["error"] * 40)))
    assert line is not None
    assert "treat the verifier as down" in line


def test_batch_health_flags_a_run_that_learned_almost_nothing():
    # One real answer in twenty is not a working verifier either.
    line = email_check.batch_health(_rows(*(["unknown"] * 19 + ["ok"])))
    assert line is not None
    assert "learned nothing about the address" in line


def test_batch_health_does_not_flag_a_run_of_real_catch_alls_with_answers():
    # catch_all is inconclusive but it IS a real reading of a real domain, so
    # a batch carrying conclusive rows alongside them is a normal batch.
    assert email_check.batch_health(
        _rows(*(["catch_all"] * 6 + ["ok", "invalid"]))) is None


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
