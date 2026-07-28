"""The offer gate's two tiers (added 2026-07-28 with The Named Fifty).

There are now two priced offers and they cannot share one gate:

  core       — The First Five (AED 2,000 + 900/call). Needs the EARNED RIGHT.
  attraction — The Named Fifty (AED 500). Needs only a LIVE THREAD.

The distinction is not price, it is whether the offer CREATES the relationship
or CONVERTS one. The failure mode this file guards against is the tempting one:
letting `--tier attraction` become a way to quote the flagship early. The tier
must be chosen by which offer is being drafted, never by which verdict the
caller wants — so `core` has to stay strict no matter what.
"""

import pytest

from audit.crm_gate import EARNED_STATUSES, REPLIED_STATUSES, check_offer


def _row(status="", asked=False):
    return {"Contact Name": "T", "Status": status, "Asked For Price": asked}


# --- core: unchanged, still the earned right --------------------------------

@pytest.mark.parametrize("status", EARNED_STATUSES)
def test_core_passes_on_every_earned_status(status):
    ok, problems, _ = check_offer(_row(status), tier="core")
    assert ok, problems


def test_core_passes_on_asked_for_price_alone():
    ok, problems, notes = check_offer(_row("Outreach Sent", asked=True), tier="core")
    assert ok, problems
    assert any("earned by ask" in n for n in notes)


def test_core_still_blocks_a_mere_reply():
    # THE regression for this change. A reply is enough for the attraction
    # offer and must NEVER become enough for the flagship.
    ok, problems, _ = check_offer(_row("Reply Received"), tier="core")
    assert not ok
    assert any("has not earned a number yet" in p for p in problems)


def test_core_failure_points_at_the_attraction_tier():
    # The person hitting this is usually drafting the wrong offer, not
    # fighting the gate. Say which one is reachable.
    _, problems, _ = check_offer(_row("Reply Received"), tier="core")
    assert any("--tier attraction" in p for p in problems)


def test_core_is_the_default_tier():
    # A caller that forgets --tier gets the STRICT gate, not the loose one.
    assert check_offer(_row("Reply Received"))[0] is False


# --- attraction: a live thread is the floor ---------------------------------

@pytest.mark.parametrize("status", REPLIED_STATUSES)
def test_attraction_passes_on_any_live_thread(status):
    ok, problems, _ = check_offer(_row(status), tier="attraction")
    assert ok, problems


def test_attraction_passes_on_asked_for_price_alone():
    ok, problems, _ = check_offer(_row("Outreach Sent", asked=True), tier="attraction")
    assert ok, problems


@pytest.mark.parametrize("status", ["", "Sourced", "Qualifying", "Audit Ready",
                                    "Draft Ready", "Outreach Sent", "Dormant"])
def test_attraction_still_refuses_a_cold_lead(status):
    # An attraction offer skips the earned right; it does not skip the human.
    # A priced offer to someone who has never replied is a cold pitch at any
    # price, and AED 500 does not make it not one.
    ok, problems, _ = check_offer(_row(status), tier="attraction")
    assert not ok, status
    assert any("LIVE THREAD" in p for p in problems)


# --- the tier itself --------------------------------------------------------

def test_unknown_tier_fails_closed():
    ok, problems, _ = check_offer(_row("Won"), tier="banana")
    assert not ok
    assert any("unknown offer tier" in p for p in problems)


def test_earned_statuses_are_a_subset_of_replied():
    # Anyone who earned the number is necessarily in a live thread, so core
    # can never pass where attraction would fail. If this ever goes red the
    # two tiers have drifted into contradiction.
    assert set(EARNED_STATUSES) <= set(REPLIED_STATUSES)


# --- output line shape ------------------------------------------------------

def test_core_keeps_the_bare_offer_label():
    # Every skill quotes this line literally and several match the exact
    # prefix, so the core tier's label must not acquire a suffix. Only the new
    # tier is allowed to look new.
    import io, json, contextlib, tempfile, os
    from audit.crm_gate import print_offer

    def _line(row, **kw):
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w") as fh:
            json.dump(row, fh)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            print_offer(path, **kw)
        os.unlink(path)
        return buf.getvalue().strip()

    assert _line(_row("Won")).startswith("CRM GATE (offer): PASS")
    assert _line(_row("Won"), tier="core").startswith("CRM GATE (offer): PASS")
    assert _line(_row("Reply Received"), tier="attraction").startswith(
        "CRM GATE (offer/attraction): PASS")
