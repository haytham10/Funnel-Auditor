"""Tests for the multi-inbox layer added 2026-07-16:

  1. audit/inboxes.py — the registry (label -> address/transport), validation,
     and the routing rule (sticky per lead, else most-headroom fill).
  2. audit/send_cap.py — now keyed by logical label, migrates the legacy flat
     and the intermediate address-keyed shapes, validates labels against the
     registry, and still fails closed PER inbox.

Run: python -m pytest tests/test_inbox_routing.py -q
     (or plain `python tests/test_inbox_routing.py` for the no-pytest path)
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audit import draft_lint, inboxes, send_cap


# --- registry -------------------------------------------------------------

def test_registry_has_labels():
    assert inboxes.labels() == ["Inbox 1", "Inbox 2"]

def test_primary_is_inbox_1():
    assert inboxes.PRIMARY_LABEL == "Inbox 1"
    assert inboxes.primary().address == "haytham@auto-mate.one"

def test_resolve_none_is_primary():
    assert inboxes.resolve(None).label == "Inbox 1"

def test_resolve_unknown_raises():
    try:
        inboxes.resolve("Inbox 9")
        assert False, "expected InboxError"
    except inboxes.InboxError:
        pass

def test_label_for_address_roundtrips():
    assert inboxes.label_for_address("haytham@gethaytham.com") == "Inbox 2"
    assert inboxes.label_for_address("HAYTHAM@AUTO-MATE.ONE") == "Inbox 1"  # case-insensitive
    assert inboxes.label_for_address("nobody@nowhere.com") is None

def test_transport_per_inbox():
    assert inboxes.resolve("Inbox 1").send_via == "gmail-mcp"
    assert inboxes.resolve("Inbox 2").send_via == "gmail-gethaytham"


# --- routing --------------------------------------------------------------

def test_route_sticky_keeps_assignment():
    # An assigned lead stays put even if the other inbox has more headroom.
    caps = {"Inbox 1": 20, "Inbox 2": 20}
    counts = {"Inbox 1": 19, "Inbox 2": 0}
    assert inboxes.choose_inbox("Inbox 1", caps, counts) == "Inbox 1"

def test_route_new_lead_picks_most_headroom():
    caps = {"Inbox 1": 20, "Inbox 2": 20}
    counts = {"Inbox 1": 18, "Inbox 2": 3}  # Inbox 2 has more room
    assert inboxes.choose_inbox(None, caps, counts) == "Inbox 2"

def test_route_ties_go_to_primary():
    caps = {"Inbox 1": 20, "Inbox 2": 20}
    counts = {"Inbox 1": 5, "Inbox 2": 5}
    assert inboxes.choose_inbox(None, caps, counts) == "Inbox 1"

def test_route_ignores_unregistered_current():
    # A stale/typo'd assignment is not sticky — it re-routes by headroom.
    caps = {"Inbox 1": 20, "Inbox 2": 20}
    counts = {"Inbox 1": 1, "Inbox 2": 10}
    assert inboxes.choose_inbox("Inbox 9", caps, counts) == "Inbox 1"

def test_route_missing_cap_counts_as_zero_headroom():
    caps = {"Inbox 1": 20}  # Inbox 2 unfunded
    counts = {"Inbox 1": 19}
    # Inbox 1 headroom 1, Inbox 2 headroom 0 -> Inbox 1 still wins
    assert inboxes.choose_inbox(None, caps, counts) == "Inbox 1"


# --- send_cap: label keys + migration + fail-closed -----------------------

def _write(tmp, obj):
    tmp.write_text(json.dumps(obj))
    return tmp

def test_cap_reads_label_keyed(tmp_path):
    p = _write(tmp_path / "c.json", {
        "primary": "Inbox 1",
        "inboxes": {"Inbox 2": {"cap": 25, "set_on": "2026-07-10", "history": []}},
    })
    st = send_cap.load_cap("Inbox 2", p)
    assert st.valid and st.cap == 25

def test_cap_migrates_flat_to_primary(tmp_path):
    p = _write(tmp_path / "c.json", {"cap": 25, "set_on": "2026-07-01", "history": []})
    st = send_cap.load_cap(None, p)  # default = primary = Inbox 1
    assert st.inbox == "Inbox 1" and st.cap == 25 and st.valid

def test_cap_migrates_address_keyed(tmp_path):
    p = _write(tmp_path / "c.json", {
        "inboxes": {"haytham@gethaytham.com": {"cap": 20, "set_on": "2026-07-16", "history": []}},
    })
    st = send_cap.load_cap("Inbox 2", p)  # address key remapped to label
    assert st.valid and st.cap == 20

def test_cap_unregistered_inbox_fails_closed(tmp_path):
    p = _write(tmp_path / "c.json", {"primary": "Inbox 1", "inboxes": {}})
    st = send_cap.load_cap("Inbox 2", p)
    assert not st.valid and st.cap == send_cap.FAIL_CLOSED_CAP and not st.registered

def test_cap_independent_per_inbox(tmp_path):
    p = _write(tmp_path / "c.json", {
        "primary": "Inbox 1",
        "inboxes": {
            "Inbox 1": {"cap": 30, "set_on": "2026-06-01", "history": []},
            "Inbox 2": {"cap": 20, "set_on": "2026-07-16", "history": []},
        },
    })
    assert send_cap.load_cap("Inbox 1", p).cap == 30
    assert send_cap.load_cap("Inbox 2", p).cap == 20

def test_set_cap_refuses_unregistered_label(tmp_path):
    p = _write(tmp_path / "c.json", {"primary": "Inbox 1", "inboxes": {}})
    ok, lines = send_cap.set_cap(20, "Inbox 9", p)
    assert not ok and "not a registered inbox" in lines[0]

def test_set_cap_registers_new_inbox_at_base(tmp_path):
    p = _write(tmp_path / "c.json", {"primary": "Inbox 1", "inboxes": {}})
    ok, _ = send_cap.set_cap(20, "Inbox 2", p)
    assert ok
    assert send_cap.load_cap("Inbox 2", p).cap == 20

def test_set_cap_refuses_new_inbox_above_base(tmp_path):
    p = _write(tmp_path / "c.json", {"primary": "Inbox 1", "inboxes": {}})
    ok, lines = send_cap.set_cap(25, "Inbox 2", p)
    assert not ok and "registers at 20" in lines[0]


# --- routing policies + warm-up weights (opt #5) --------------------------

def test_policy_fill_primary_fills_primary_first():
    caps = {"Inbox 1": 20, "Inbox 2": 20}
    counts = {"Inbox 1": 5, "Inbox 2": 0}  # headroom would pick Inbox 2; fill-primary keeps Inbox 1
    assert inboxes.choose_inbox(None, caps, counts, policy="fill-primary") == "Inbox 1"

def test_policy_fill_primary_overflows_when_primary_full():
    caps = {"Inbox 1": 20, "Inbox 2": 20}
    counts = {"Inbox 1": 20, "Inbox 2": 0}
    assert inboxes.choose_inbox(None, caps, counts, policy="fill-primary") == "Inbox 2"

def test_warmup_weight_biases_away_from_young_inbox():
    caps = {"Inbox 1": 20, "Inbox 2": 20}
    counts = {"Inbox 1": 12, "Inbox 2": 0}  # raw headroom: I1=8, I2=20 -> I2
    # Weight Inbox 2 down to 0.3: effective I2 = 20*0.3 = 6 < I1 = 8 -> Inbox 1 wins
    assert inboxes.choose_inbox(None, caps, counts, weights={"Inbox 2": 0.3}) == "Inbox 1"

def test_sticky_beats_policy_and_weights():
    caps = {"Inbox 1": 20, "Inbox 2": 20}
    counts = {"Inbox 1": 19, "Inbox 2": 0}
    assert inboxes.choose_inbox("Inbox 2", caps, counts, policy="fill-primary") == "Inbox 2"


def test_unknown_policy_raises():
    try:
        inboxes.choose_inbox(None, {"Inbox 1": 20}, {}, policy="round-robin")
        assert False, "expected InboxError"
    except inboxes.InboxError:
        pass

def test_negative_headroom_clamped_before_weighting():
    # Both over cap. Without the clamp, Inbox 2's <1 weight would make its
    # negative headroom LESS negative (-2 x 0.3 = -0.6 beats -1), flipping
    # the warm-up bias toward the exact inbox it protects.
    caps = {"Inbox 1": 20, "Inbox 2": 20}
    counts = {"Inbox 1": 21, "Inbox 2": 22}
    got = inboxes.choose_inbox(None, caps, counts, weights={"Inbox 2": 0.3})
    assert got == "Inbox 1"  # all clamped to 0 -> tie -> primary

def test_dubai_midnight_epoch_roundtrips():
    from datetime import date, datetime
    epoch = send_cap.dubai_midnight_epoch(date(2026, 7, 16))
    back = datetime.fromtimestamp(epoch, send_cap.DUBAI_TZ)
    assert (back.year, back.month, back.day, back.hour, back.minute) == (2026, 7, 16, 0, 0)

def test_set_cap_refuses_rewrite_over_corrupt_file(tmp_path):
    p = tmp_path / "c.json"
    p.write_text("{ this is not json")
    ok, lines = send_cap.set_cap(20, "Inbox 1", p)
    assert not ok and "not readable JSON" in lines[0]
    assert p.read_text() == "{ this is not json"  # untouched

def test_gethaytham_draft_lints_subject_before_any_network():
    # A dirty subject must raise the copy-rules error BEFORE the transport
    # ever touches credentials or the network.
    from audit import gmail_gethaytham as gg
    try:
        gg.create_draft("x@y.com", "one thing — quick", "clean body. Haytham")
        assert False, "expected GmailGethaythamError"
    except gg.GmailGethaythamError as e:
        assert "copy rules" in str(e) and "em-dash" in str(e)


# --- reconcile (opt #3) ---------------------------------------------------

def test_reconcile_match_no_change():
    needs, corrected, _ = inboxes.reconcile_assignment("Inbox 1", "Inbox 1")
    assert not needs and corrected == "Inbox 1"

def test_reconcile_mismatch_reality_wins():
    needs, corrected, _ = inboxes.reconcile_assignment("Inbox 1", "Inbox 2")
    assert needs and corrected == "Inbox 2"

def test_reconcile_blank_current_sets_found():
    needs, corrected, _ = inboxes.reconcile_assignment(None, "Inbox 2")
    assert needs and corrected == "Inbox 2"

def test_reconcile_unknown_found_is_noop():
    needs, corrected, _ = inboxes.reconcile_assignment("Inbox 1", "Inbox 9")
    assert not needs and corrected == "Inbox 1"


# --- draft lint: shared bare-link + em-dash rule (opt #1) -----------------

def test_lint_clean_body_passes():
    assert draft_lint.scan("Hey, saw your old site and had one quick thought. Haytham") == []

def test_lint_bare_domain_flagged():
    problems = draft_lint.scan("check drsusankoruthu.com for the issue")
    assert problems and "auto-link" in problems[0]

def test_lint_bare_email_flagged():
    assert draft_lint.scan("reply to jane@coach.ae") != []

def test_lint_scheme_link_allowed():
    assert draft_lint.scan("proof here: https://haytham-sys.netlify.app/x") == []

def test_lint_em_dash_flagged():
    problems = draft_lint.scan("one thing — it matters")
    assert any("em-dash" in p for p in problems)

def test_lint_allowlisted_bare_domain_ok():
    assert draft_lint.scan("see haytham-sys.netlify.app") == []


# --- deliverability log appender (opt #4) ---------------------------------

def _log_fixture(tmp_path):
    p = tmp_path / "log.md"
    p.write_text("# Deliverability log\n\nblurb\n\n## Log\n\n- 2026-07-15 — [Inbox 1] — [note] — seed\n")
    return p

def test_log_append_prepends_under_anchor(tmp_path):
    from datetime import date
    p = _log_fixture(tmp_path)
    ok, msg = send_cap.append_log_entry("Inbox 2", "bounce", "a@b.com  hard   bounce",
                                        on=date(2026, 7, 16), path=p)
    assert ok
    body = p.read_text()
    # newest entry is the first bullet after the anchor, whitespace-collapsed
    first = body.split("## Log\n\n", 1)[1].splitlines()[0]
    assert first == "- 2026-07-16 — [Inbox 2] — [bounce] — a@b.com hard bounce"
    assert "seed" in body  # old entry preserved

def test_log_append_refuses_unknown_inbox(tmp_path):
    p = _log_fixture(tmp_path)
    ok, msg = send_cap.append_log_entry("Inbox 9", "note", "x", path=p)
    assert not ok and "not a registered inbox" in msg

def test_log_append_refuses_unknown_kind(tmp_path):
    p = _log_fixture(tmp_path)
    ok, msg = send_cap.append_log_entry("Inbox 1", "explosion", "x", path=p)
    assert not ok and "unknown" in msg


# --- no-pytest fallback ---------------------------------------------------

if __name__ == "__main__":
    import tempfile, pathlib, traceback
    passed = failed = 0
    for name, fn in sorted(globals().items()):
        if not (name.startswith("test_") and callable(fn)):
            continue
        try:
            if "tmp_path" in fn.__code__.co_varnames[: fn.__code__.co_argcount]:
                with tempfile.TemporaryDirectory() as d:
                    fn(pathlib.Path(d))
            else:
                fn()
            passed += 1
        except Exception:
            failed += 1
            print(f"FAIL {name}")
            traceback.print_exc()
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
