"""Tests for the command-center dashboard (audit/dashboard.py):

  1. build_skeleton() — the Python-reachable base snapshot: required keys,
     null-seeded panels, and the fail-closed sent-today count for the
     direct-API inbox when its credentials are absent.
  2. validate_snapshot() — rejects a snapshot missing the load-bearing core.
  3. render_html() — produces a self-contained page (no external assets) from
     a full fixture, and degrades to empty states on a skeleton-only snapshot.

Hermetic: no network. The one gethaytham path is exercised with its env
credentials cleared, so it raises before any HTTP call (same guarantee as
tests/test_inbox_routing.py's gethaytham test).

Run: python -m pytest tests/test_dashboard.py -q
     (or plain `python tests/test_dashboard.py` for the no-pytest path)
"""

import os
import sys
from contextlib import contextmanager

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audit import dashboard


@contextmanager
def _no_gethaytham_creds():
    """Clear the three gethaytham OAuth env vars for the duration, so the
    direct Gmail API path fails closed on missing creds (no network)."""
    names = (
        "GETHAYTHAM_GMAIL_CLIENT_ID",
        "GETHAYTHAM_GMAIL_CLIENT_SECRET",
        "GETHAYTHAM_GMAIL_REFRESH_TOKEN",
    )
    saved = {n: os.environ.pop(n, None) for n in names}
    try:
        yield
    finally:
        for n, v in saved.items():
            if v is not None:
                os.environ[n] = v


def _full_snapshot():
    """A completed snapshot with every panel filled — the shape the /dashboard
    skill produces before calling render."""
    return {
        "generated_at": "2026-07-16T14:30:00+04:00",
        "generated_day": "2026-07-16",
        "timezone": "Asia/Dubai (UTC+4)",
        "cap_total": 45,
        "inboxes": [
            {"label": "Inbox 1", "address": "haytham@auto-mate.one",
             "send_via": "gmail-mcp", "primary": True, "cap": 25,
             "sent_today": 20, "sent_scheduled": 2, "count_source": "gmail-mcp",
             "ramp": {"valid": True, "status_lines": ["SEND CAP [Inbox 1]: 25/day", "next step 30/day"]}},
            {"label": "Inbox 2", "address": "haytham@gethaytham.com",
             "send_via": "gmail-gethaytham", "primary": False, "cap": 20,
             "sent_today": 21, "sent_scheduled": 0, "count_source": "python",
             "ramp": {"valid": True, "status_lines": ["SEND CAP [Inbox 2]: 20/day"]}},
        ],
        "pipeline": {"by_status": {
            "Sourced": 12, "Qualifying": 5, "Audit Ready": 3, "Outreach Sent": 8,
            "Reply Received": 2, "Won": 1, "Lost": 4, "Dormant": 6,
            "Some New Status": 1,  # an unknown status must still surface
        }},
        "replies": [{"name": "Jane Coach", "status": "Reply Received",
                     "last_contacted": "2026-07-15", "note": "asked about price"}],
        "discovery_ladder": {
            "due_question": [{"name": "Sam", "status": "Reply Received", "next_action": "2026-07-16"}],
            "offer_unlocked": [{"name": "Lee", "anchor": "At 735 AED", "answer": "around 700 dirhams"}],
        },
        "due_followups": [{"name": "Ari", "touch": 2, "inbox": "Inbox 1",
                           "carries": "second-finding", "next_action": "2026-07-16"}],
        "send_queue": [
            {"name": "Nadia", "status": "Draft Ready", "inbox": "Inbox 1",
             "finding_verified": "yes", "email_verified": "yes"},
            {"name": "Omar", "status": "Audit Ready", "inbox": "Inbox 2",
             "finding_verified": "yes", "email_verified": "no"},
        ],
        "price_discovery": {
            "anchors": {"Above 735 AED": 2, "At 735 AED": 3, "Below 735 AED": 1, "Refused to name": 1},
            "est_value": {"Track A ($200)": 4, "Track B ($700)": 2},
        },
        "scoreboard": {"Leads cold-touched": 14, "Reply rate": "12%",
                       "Discovery answers": 3, "Offers": 1, "Closes": 0},
        "hygiene": ["Inbox 2 is 1 over ceiling today", "1 lead Draft Ready 6 days, no send"],
    }


# --- build_skeleton -------------------------------------------------------

def test_skeleton_has_required_keys():
    with _no_gethaytham_creds():
        snap = dashboard.build_skeleton()
    for key in dashboard.SNAPSHOT_KEYS:
        assert key in snap, f"missing {key}"
    assert isinstance(snap["inboxes"], list) and snap["inboxes"]

def test_skeleton_seeds_panels_null():
    with _no_gethaytham_creds():
        snap = dashboard.build_skeleton()
    # Every skill-filled panel is present but null, so the skill fills in place.
    for panel in ("pipeline", "replies", "send_queue", "scoreboard", "hygiene"):
        assert panel in snap and snap[panel] is None

def test_skeleton_cap_total_is_sum():
    with _no_gethaytham_creds():
        snap = dashboard.build_skeleton()
    assert snap["cap_total"] == sum(m["cap"] for m in snap["inboxes"])

def test_skeleton_mcp_inbox_count_is_null_with_query():
    with _no_gethaytham_creds():
        snap = dashboard.build_skeleton()
    mcp = [m for m in snap["inboxes"] if m["send_via"] == "gmail-mcp"]
    assert mcp, "expected at least one Gmail-MCP inbox"
    for m in mcp:
        assert m["sent_today"] is None
        assert m["count_source"] == "gmail-mcp"
        assert m["count_query"].startswith("in:sent after:")

def test_skeleton_gethaytham_fails_closed_without_creds():
    # Direct-API inbox with no creds: sent_today must be null (never a fake 0),
    # and it must not have hit the network to learn that.
    with _no_gethaytham_creds():
        snap = dashboard.build_skeleton()
    direct = [m for m in snap["inboxes"] if m["send_via"] == "gmail-gethaytham"]
    assert direct, "expected the gethaytham inbox in the registry"
    for m in direct:
        assert m["sent_today"] is None
        assert m["count_source"] == "python"
        assert "count_error" in m  # the missing-creds message, caught not raised


# --- validate_snapshot ----------------------------------------------------

def test_validate_rejects_non_dict():
    try:
        dashboard.validate_snapshot([1, 2, 3])
        assert False, "expected DashboardError"
    except dashboard.DashboardError:
        pass

def test_validate_rejects_missing_key():
    try:
        dashboard.validate_snapshot({"generated_at": "x", "generated_day": "y", "cap_total": 0})
        assert False, "expected DashboardError (no inboxes)"
    except dashboard.DashboardError as e:
        assert "inboxes" in str(e)

def test_validate_rejects_empty_inboxes():
    snap = {"generated_at": "x", "generated_day": "y", "cap_total": 0, "inboxes": []}
    try:
        dashboard.validate_snapshot(snap)
        assert False, "expected DashboardError"
    except dashboard.DashboardError:
        pass

def test_validate_accepts_full_snapshot():
    dashboard.validate_snapshot(_full_snapshot())  # must not raise


# --- render_html ----------------------------------------------------------

def test_render_contains_every_panel():
    out = dashboard.render_html(_full_snapshot())
    for marker in ("Sending inboxes", "Pipeline", "Replies", "Send queue",
                   "Discovery ladder", "Follow-ups due", "Price discovery study",
                   "Weekly scoreboard", "Hygiene alerts"):
        assert marker in out, f"panel missing: {marker}"

def test_render_is_self_contained():
    out = dashboard.render_html(_full_snapshot())
    # No external assets — the Artifact CSP forbids them.
    assert "<title>" in out
    assert "https://" not in out and "http://" not in out
    assert "<link " not in out
    assert "<script src" not in out and "src=" not in out

def test_render_surfaces_unknown_status():
    out = dashboard.render_html(_full_snapshot())
    assert "Some New Status" in out  # unknown statuses surface, never silently dropped

def test_render_flags_over_ceiling():
    out = dashboard.render_html(_full_snapshot())
    assert "OVER CEILING" in out  # Inbox 2 sent 21 > cap 20

def test_render_escapes_html():
    snap = _full_snapshot()
    snap["replies"] = [{"name": "<script>alert(1)</script>", "status": "x",
                        "last_contacted": "y", "note": "z"}]
    out = dashboard.render_html(snap)
    assert "<script>alert(1)</script>" not in out
    assert "&lt;script&gt;" in out

def test_render_skeleton_degrades_to_empty_states():
    with _no_gethaytham_creds():
        snap = dashboard.build_skeleton()
    out = dashboard.render_html(snap)
    assert "Sending inboxes" in out  # the Python-filled panel renders
    assert "Awaiting" in out  # the null skill panels show empty states, not a crash

def test_render_bad_snapshot_raises():
    try:
        dashboard.render_html({"nope": True})
        assert False, "expected DashboardError"
    except dashboard.DashboardError:
        pass


# --- no-pytest fallback ---------------------------------------------------

if __name__ == "__main__":
    import traceback
    passed = failed = 0
    for name, fn in sorted(globals().items()):
        if not (name.startswith("test_") and callable(fn)):
            continue
        try:
            fn()
            passed += 1
        except Exception:
            failed += 1
            print(f"FAIL {name}")
            traceback.print_exc()
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
