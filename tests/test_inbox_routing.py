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

from audit import inboxes, send_cap


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
