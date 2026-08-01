"""The local email gate: `check_email` and the `verify_local` wrapper over it.

This is the whole offline check — syntax, the never-send/typo/disposable lists,
the three-way MX ladder, and role detection — and until now it had **no tests at
all**, which is how it came to be the documented fallback for a paid verifier
that nobody had ever exercised. The ZeroBounce module it replaced turned out to
have zero credits the day the outage called on it.

Every DNS path is stubbed. A test that reaches the network is a test that fails
on a bad day for reasons that have nothing to do with the code.

Run: python -m pytest tests/test_email_local.py -q
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audit import email_check


@pytest.fixture
def dns(monkeypatch):
    """Pin the MX ladder. `set(method, hosts)` decides what every lookup in the
    test sees; the two lower rungs are disabled so nothing falls through to a
    real resolver."""
    state = {"result": ("MX", ["aspmx.l.google.com"])}

    def _set(method, hosts=()):
        state["result"] = (method, list(hosts))

    monkeypatch.setattr(email_check, "_mx_via_dnspython", lambda d: state["result"])
    monkeypatch.setattr(email_check, "_mx_via_nslookup", lambda d: None)
    monkeypatch.setattr(email_check, "_mx_via_socket", lambda d: ("NXDOMAIN", []))
    return _set


# --- check_email, the gate itself -------------------------------------------


def test_a_personal_address_on_a_domain_with_mx_passes(dns):
    verdict, details = email_check.check_email("jane@janedoe.ae")
    assert verdict == "PASS"
    assert "MX ok (aspmx.l.google.com)" in details
    assert "personal" in details


def test_a_bad_shape_fails_before_any_lookup(dns):
    dns("NXDOMAIN")
    verdict, details = email_check.check_email("not-an-address")
    assert verdict == "FAIL"
    assert "valid address shape" in details[0]


def test_a_no_reply_local_fails(dns):
    verdict, details = email_check.check_email("no-reply@janedoe.ae")
    assert verdict == "FAIL"
    assert "nothing human reads it" in details[0]


def test_a_typo_domain_fails_and_names_the_fix(dns):
    verdict, details = email_check.check_email("jane@gmial.com")
    assert verdict == "FAIL"
    assert "jane@gmail.com" in details[0]


def test_a_disposable_domain_fails(dns):
    verdict, details = email_check.check_email("jane@mailinator.com")
    assert verdict == "FAIL"
    assert "disposable" in details[0]


def test_a_domain_that_does_not_resolve_fails(dns):
    dns("NXDOMAIN")
    verdict, details = email_check.check_email("jane@nowhere.invalid")
    assert verdict == "FAIL"
    assert "cannot receive mail" in details[0]


def test_an_a_record_fallback_warns_rather_than_passing(dns):
    # RFC 5321 says an A record can accept mail, but it is a soft signal and
    # this gate exists because a guessed address bounced against a live domain.
    dns("A-fallback", ["janedoe.ae"])
    verdict, details = email_check.check_email("jane@janedoe.ae")
    assert verdict == "WARN"
    assert any("A-record fallback" in d for d in details)


def test_a_domain_with_no_mail_setup_warns(dns):
    dns("none")
    assert email_check.check_email("jane@janedoe.ae")[0] == "WARN"


def test_a_role_address_downgrades_a_pass_to_warn(dns):
    verdict, details = email_check.check_email("info@janedoe.ae")
    assert verdict == "WARN"
    assert any("role account" in d for d in details)


def test_the_name_match_is_a_note_and_never_a_verdict(dns):
    verdict, details = email_check.check_email("jane@janedoe.ae", "Jane Doe")
    assert verdict == "PASS"
    assert "matches lead name" in details
    # And its absence changes nothing about the verdict.
    assert email_check.check_email("hello.there@janedoe.ae", "Jane Doe")[0] == "PASS"


def test_an_initial_is_too_short_to_count_as_a_name_match(dns):
    # `name_tokens(min_len=3)` — "j" inside any local part would match
    # everything, which is the same as matching nothing.
    _, details = email_check.check_email("jsmith@corp.ae", "J Smith")
    assert "matches lead name" in details      # "smith" carries it
    _, details = email_check.check_email("bob@corp.ae", "J Smith")
    assert "matches lead name" not in details


# --- verify_local, the fallback wrapper -------------------------------------


def test_verify_local_returns_one_row_per_address_in_order(dns):
    rows = email_check.verify_local(["a@x.ae", "b@y.ae", "c@z.ae"])
    assert [r["email"] for r in rows] == ["a@x.ae", "b@y.ae", "c@z.ae"]


def test_verify_local_never_claims_a_mailbox_exists(dns):
    # The whole contract. A domain with perfect MX is still only local_mx,
    # which classifies to WARN, which can never check `Email Verified`.
    row = email_check.verify_local(["jane@janedoe.ae"])[0]
    assert row["result"] == "local_mx"
    assert email_check.classify_verification(row)[0] == "WARN"


def test_verify_local_says_who_answered(dns):
    assert email_check.verify_local(["jane@janedoe.ae"])[0]["verified_by"] == "local"


def test_verify_local_fails_are_real_fails(dns):
    dns("NXDOMAIN")
    row = email_check.verify_local(["jane@nowhere.invalid"])[0]
    assert row["result"] == "invalid"
    assert email_check.classify_verification(row)[0] == "FAIL"


def test_verify_local_keeps_disposable_as_its_own_reason(dns):
    # Not folded into `invalid`: the classifier's `invalid` message says
    # "mailbox does not exist", which is not what is wrong with mailinator.
    row = email_check.verify_local(["jane@mailinator.com"])[0]
    assert row["result"] == "disposable"
    assert email_check.classify_verification(row)[0] == "FAIL"


def test_verify_local_carries_the_reason_the_gate_gave(dns):
    row = email_check.verify_local(["jane@gmial.com"])[0]
    assert "jane@gmail.com" in row["reason"]


def test_verify_local_flags_a_role_address(dns):
    assert email_check.verify_local(["info@janedoe.ae"])[0]["role"] is True
    assert email_check.verify_local(["jane@janedoe.ae"])[0]["role"] is False


def test_a_whole_local_batch_is_not_reported_as_an_outage(dns):
    # Every local row is `local_mx`, which is in the "learned nothing" set, so
    # the naive rule fires on every local run — and a check that always fires
    # is one people learn to ignore. An all-local run is the documented
    # behaviour of a chosen provider, not a fault.
    rows = email_check.verify_local([f"a{i}@x.ae" for i in range(8)])
    assert email_check.batch_health(rows) is None


def test_a_local_row_leaking_into_a_paid_run_is_still_flagged(dns):
    # The exemption is for a run that is local by construction. A paid run that
    # learned nothing is still an outage, whatever is mixed into it.
    rows = email_check.verify_local([f"a{i}@x.ae" for i in range(7)])
    rows.append({"email": "b@y.ae", "result": "error", "verified_by": "apify"})
    assert email_check.batch_health(rows) is not None
