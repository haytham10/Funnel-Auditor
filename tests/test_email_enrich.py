"""Tests for nominative email enrichment (audit/email_enrich.py).

Two halves, mirroring the existing suites:
  1. candidate_locals — the pure name -> ranked-locals generator.
  2. enrich — the convergence logic, with the verifier INJECTED (canned rows),
     so the network / Apify layer is never touched. This is where the three
     safety properties are proven: exactly-one-address, catch-all never PASSes,
     free-provider domains are refused.

Run: python -m pytest tests/test_email_enrich.py -q
     (or plain `python tests/test_email_enrich.py` for the no-pytest path)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audit import email_enrich


# --- candidate_locals ------------------------------------------------------

def test_candidate_locals_two_tokens_ranked():
    got = email_enrich.candidate_locals("Jane Doe")
    assert got == ["jane", "jane.doe", "janedoe", "jdoe",
                   "jane_doe", "janed", "j.doe", "doe"]


def test_candidate_locals_single_token_is_just_first():
    assert email_enrich.candidate_locals("Cher") == ["cher"]


def test_candidate_locals_three_tokens_uses_first_and_last():
    got = email_enrich.candidate_locals("Mary Jane Watson")
    assert got[0] == "mary"
    assert "mary.watson" in got
    assert "mwatson" in got
    assert "watson" in got


def test_candidate_locals_hyphenated_name_splits():
    # A hyphen is a non-letter, so it splits into two tokens.
    got = email_enrich.candidate_locals("Anne-Marie Cox")
    assert got[0] == "anne"
    assert "anne.cox" in got


def test_candidate_locals_accented_name_folds_to_ascii():
    got = email_enrich.candidate_locals("José García")
    assert got[0] == "jose"
    assert "jose.garcia" in got
    # no non-ascii leaked into any candidate
    assert all(c.isascii() for local in got for c in local)


def test_candidate_locals_short_first_name_kept():
    # A two-letter first name is a real local part — min_len=1 must keep it.
    got = email_enrich.candidate_locals("Li Wei")
    assert got[0] == "li"


def test_candidate_locals_empty_name_is_empty():
    assert email_enrich.candidate_locals("") == []
    assert email_enrich.candidate_locals("   ") == []


def test_candidate_locals_deduped_no_empties():
    got = email_enrich.candidate_locals("Jane Doe")
    assert len(got) == len(set(got))
    assert all(got)


# --- enrich: convergence + safety (verifier injected) ----------------------

def _rows(mapping):
    """Build canned verifier rows: {address: result_token} -> list[dict]."""
    return [{"email": addr, "result": token} for addr, token in mapping.items()]


# A shape check that always passes — keeps the DNS/MX layer (check_email) out of
# these tests, so they exercise pure convergence logic offline. Injected as
# `shape_check` everywhere below.
_PASS_SHAPE = lambda addr, name: ("PASS", ["MX ok (test)", "personal"])


def test_enrich_single_pass_is_adopted():
    def verifier(cands):
        # only jane.doe@ is deliverable; the rest don't exist
        return _rows({c: ("ok" if c == "jane.doe@janedoe.com" else "invalid")
                      for c in cands})

    r = email_enrich.enrich("Jane Doe", "https://janedoe.com/",
                            verifier=verifier, shape_check=_PASS_SHAPE)
    assert r["verdict"] == "PASS"
    assert r["address"] == "jane.doe@janedoe.com"
    assert r["pattern"] == "first.last@"
    assert r["discarded"] == []


def test_enrich_two_pass_adopts_exactly_one_top_ranked():
    # Both first@ and first.last@ verify. The single-address rule: adopt the
    # top-ranked (first@), the other is discarded, never a second sendable addr.
    def verifier(cands):
        return _rows({c: ("ok" if c in ("jane@janedoe.com", "jane.doe@janedoe.com")
                          else "invalid") for c in cands})

    r = email_enrich.enrich("Jane Doe", "janedoe.com", verifier=verifier, shape_check=_PASS_SHAPE)
    assert r["verdict"] == "PASS"
    assert r["address"] == "jane@janedoe.com"          # top-ranked
    assert r["discarded"] == ["jane.doe@janedoe.com"]  # the other PASS, not used


def test_enrich_catch_all_domain_holds_never_passes():
    # Every candidate answers catch_all -> WARN. No mailbox confirmable: HOLD,
    # nothing adopted. This is the core safety property.
    def verifier(cands):
        return _rows({c: "catch_all" for c in cands})

    r = email_enrich.enrich("Jane Doe", "janedoe.com", verifier=verifier, shape_check=_PASS_SHAPE)
    assert r["verdict"] == "HOLD"
    assert r["address"] is None


def test_enrich_all_invalid_is_none():
    def verifier(cands):
        return _rows({c: "invalid" for c in cands})

    r = email_enrich.enrich("Jane Doe", "janedoe.com", verifier=verifier, shape_check=_PASS_SHAPE)
    assert r["verdict"] == "NONE"
    assert r["address"] is None


def test_enrich_free_provider_domain_refused_without_verifying():
    calls = []

    def verifier(cands):
        calls.append(cands)
        return _rows({c: "ok" for c in cands})

    r = email_enrich.enrich("Jane Doe", "jane@gmail.com", verifier=verifier)
    assert r["verdict"] == "NONE"
    assert "free-provider" in r["reason"]
    assert calls == []  # never spent a verify call on a free-provider domain


def test_enrich_verifier_reordered_rows_still_ranks_by_candidate_order():
    # Verifier returns rows out of order / with extra whitespace-cased emails.
    def verifier(cands):
        return [{"email": "JANE.DOE@janedoe.com ", "result": "ok"},
                {"email": "jane@janedoe.com", "result": "ok"}]

    r = email_enrich.enrich("Jane Doe", "janedoe.com", verifier=verifier, shape_check=_PASS_SHAPE)
    assert r["verdict"] == "PASS"
    assert r["address"] == "jane@janedoe.com"  # rank order, not row order


def test_enrich_empty_name_is_none():
    r = email_enrich.enrich("", "janedoe.com", verifier=lambda c: [])
    assert r["verdict"] == "NONE"


def test_print_enrich_exit_codes():
    ok_verifier = lambda c: _rows({c[0]: "ok", **{x: "invalid" for x in c[1:]}})
    assert email_enrich.print_enrich("Jane Doe", "janedoe.com",
                                     verifier=ok_verifier, shape_check=_PASS_SHAPE) == 0
    none_verifier = lambda c: _rows({x: "invalid" for x in c})
    assert email_enrich.print_enrich("Jane Doe", "janedoe.com",
                                     verifier=none_verifier, shape_check=_PASS_SHAPE) == 1


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
