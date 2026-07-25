"""
The inbox registry — the ONE place that maps a logical inbox label
("Inbox 1", "Inbox 2", ...) to its real sending address, its send/read
mechanism, and its ramp identity.

Everything else in the system speaks the LOGICAL LABEL, never the raw
address: the CRM's `Inbox` property, `send_cap.json`'s keys, the
`crm-gate send --inbox` flag, and the tick's per-inbox counting. Only this
module knows that "Inbox 1" is haytham@auto-mate.one reached through the
Gmail MCP connector, and that "Inbox 2" is haytham@gethaytham.com reached
through the direct Gmail API path (`main.py gmail-gethaytham`). That
indirection is deliberate: it means the address, credentials, or transport
behind a label can change without touching a single lead row, a cap entry,
or a routine — the label is the stable contract.

## Scaling to Inbox 3, 4, N

Add ONE entry to `_REGISTRY` below, register its ceiling
(`python main.py send-cap set 20 --inbox "Inbox 3"`), and add the option to
the CRM's `Inbox` select. Routing, counting, gating, and the CLI all read
this registry, so nothing else has a hardcoded "two inboxes" assumption.
The hard rules still hold per inbox: each is its own domain, ramps 20→25→30
on its own reputation, and 30 is the ceiling for ONE inbox.

## Send/read transport per inbox (`send_via`)

  gmail-mcp        — reached through the Claude Gmail MCP connector already
                     bound to this account (search_threads / list_drafts /
                     create_draft, etc.). This is the primary inbox.
  gmail-gethaytham — reached through the direct Gmail REST path in
                     audit/gmail_gethaytham.py, driven by
                     `python main.py gmail-gethaytham <search|drafts|draft|...>`.
                     Used because Claude binds only one connector to Google's
                     single Gmail MCP endpoint (see that module's docstring).

A skill or routine that reads sent counts, sweeps for replies, or creates a
draft for a given lead branches on `resolve(label).send_via`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


class InboxError(ValueError):
    """Raised when a label is not a registered inbox."""


@dataclass(frozen=True)
class Inbox:
    label: str          # the logical name used everywhere (CRM, cap file, CLI)
    address: str        # the real sending address behind the label
    send_via: str       # transport: "gmail-mcp" | "gmail-gethaytham"
    is_primary: bool    # the default when nothing selects an inbox
    note: str = ""      # short human description for `inbox list`


# ---------------------------------------------------------------------------
# THE REGISTRY. To add an inbox, add a row here (and register its cap + the
# CRM select option). Order matters: it is the tie-break order for routing
# and the display order for `inbox list`. Exactly one entry is primary.
# ---------------------------------------------------------------------------
_REGISTRY: tuple[Inbox, ...] = (
    Inbox(
        label="Inbox 1",
        address="haytham@auto-mate.one",
        send_via="gmail-mcp",
        is_primary=True,
        note="original UAE + parenting inbox; Gmail MCP connector",
    ),
    Inbox(
        label="Inbox 2",
        address="haytham@gethaytham.com",
        send_via="gmail-gethaytham",
        is_primary=False,
        note="second UAE inbox; direct Gmail API (main.py gmail-gethaytham)",
    ),
)

# Fail loudly at import if the registry is malformed — one and only one
# primary, unique labels and addresses. These are invariants the rest of the
# system relies on, not runtime conditions to handle gracefully. Explicit
# raises, not asserts: asserts vanish under `python -O` and this is a safety
# file.
_PRIMARIES = [ib for ib in _REGISTRY if ib.is_primary]
if len(_PRIMARIES) != 1:
    raise RuntimeError(f"inbox registry must have exactly one primary inbox, found {len(_PRIMARIES)}")

PRIMARY_LABEL: str = _PRIMARIES[0].label


def _has_direct_gmail_credentials() -> bool:
    generic = (
        os.environ.get("GMAIL_CLIENT_ID"),
        os.environ.get("GMAIL_CLIENT_SECRET"),
        os.environ.get("GMAIL_REFRESH_TOKEN"),
    )
    if all(generic):
        return True
    inbox1 = (
        os.environ.get("INBOX1_GMAIL_CLIENT_ID"),
        os.environ.get("INBOX1_GMAIL_CLIENT_SECRET"),
        os.environ.get("INBOX1_GMAIL_REFRESH_TOKEN"),
    )
    return all(inbox1)


def _runtime_registry() -> tuple[Inbox, ...]:
    if not _has_direct_gmail_credentials():
        return _REGISTRY
    return tuple(
        Inbox(
            label=ib.label,
            address=ib.address,
            send_via="gmail-gethaytham" if ib.label == "Inbox 1" else ib.send_via,
            is_primary=ib.is_primary,
            note=(
                "direct Gmail API fallback for Inbox 1; Gmail MCP unavailable"
                if ib.label == "Inbox 1"
                else ib.note
            ),
        )
        for ib in _REGISTRY
    )


def _runtime_by_label() -> dict[str, Inbox]:
    return {ib.label: ib for ib in _runtime_registry()}


def _runtime_by_address() -> dict[str, Inbox]:
    return {ib.address.lower(): ib for ib in _runtime_registry()}


def labels() -> list[str]:
    """All registered inbox labels, in registry order."""
    return [ib.label for ib in _runtime_registry()]


def all_inboxes() -> list[Inbox]:
    return list(_runtime_registry())


def is_registered(label: str | None) -> bool:
    return label in _runtime_by_label()


def resolve(label: str | None) -> Inbox:
    """The Inbox for a label; the primary when label is None/empty.

    Raises InboxError on an unknown non-empty label — callers that must fail
    closed instead (e.g. the cap loader) should check is_registered first.
    """
    by_label = _runtime_by_label()
    if not label:
        return by_label[PRIMARY_LABEL]
    ib = by_label.get(label)
    if ib is None:
        raise InboxError(
            f"{label!r} is not a registered inbox. Known: {', '.join(labels())}. "
            "Add it to audit/inboxes.py first."
        )
    return ib


def primary() -> Inbox:
    return _runtime_by_label()[PRIMARY_LABEL]


def label_for_address(address: str | None) -> str | None:
    """The logical label behind a raw address, or None if unregistered."""
    if not address:
        return None
    ib = _runtime_by_address().get(address.lower())
    return ib.label if ib else None


ROUTING_POLICIES = ("headroom", "fill-primary")


def choose_inbox(
    current: str | None,
    caps: dict[str, int],
    counts: dict[str, int],
    policy: str = "headroom",
    weights: dict[str, float] | None = None,
) -> str:
    """The routing rule — which inbox a lead's next send leaves from.

    STICKY per lead: once a lead has a valid registered assignment, it keeps
    it, so an entire thread (opener + follow-ups + the warm exchange) stays
    on one domain — clean for reply threading and for attributing which
    domain earned a reply or a bounce.

    New/unassigned leads are routed by `policy`:
      - "headroom" (default): the inbox with the most remaining headroom
        today (cap − sends so far), ties broken by registry order (primary
        first). Spreads new openers across inboxes as capacity grows.
      - "fill-primary": the FIRST inbox (registry order) that still has
        headroom today — fill primary, then overflow. Concentrates
        reputation on one domain until it's full each day.

    `weights` (optional) scales effective headroom per label for warm-up
    biasing: give a young inbox a weight < 1 so it's chosen LESS while its
    reputation is still building (e.g. {"Inbox 2": 0.3}). Missing label = 1.0.
    Applies to the "headroom" policy.

    This function is the single knob for routing policy — adding a new policy
    (track-based, round-robin, ...) is a change here and nowhere else. An
    unknown policy raises rather than silently falling back: a typo'd policy
    quietly rerouting leads is exactly the kind of leak this layer exists to
    prevent.

    caps/counts are keyed by label; a missing entry is treated as cap 0 /
    count 0 so an unregistered-or-unfunded inbox is never chosen for new work.
    """
    if policy not in ROUTING_POLICIES:
        raise InboxError(f"unknown routing policy {policy!r} (one of: {', '.join(ROUTING_POLICIES)})")

    if is_registered(current):
        return current  # sticky

    if policy == "fill-primary":
        for label in labels():  # registry order
            if caps.get(label, 0) - counts.get(label, 0) > 0:
                return label
        return PRIMARY_LABEL

    # "headroom" (default), optionally warm-up-weighted. Headroom is clamped
    # at 0 BEFORE weighting: on a negative number a <1 weight would flip the
    # bias and favor the exact inbox it's meant to protect (-2 x 0.3 = -0.6
    # beats -1). A full inbox has zero room, not negative attractiveness.
    weights = weights or {}
    best_label = PRIMARY_LABEL
    best_score = None
    for label in labels():  # registry order → primary wins ties
        headroom = max(caps.get(label, 0) - counts.get(label, 0), 0)
        score = headroom * weights.get(label, 1.0)
        if best_score is None or score > best_score:
            best_score = score
            best_label = label
    return best_label


def reconcile_assignment(current: str | None, found_in: str | None) -> tuple[bool, str | None, str]:
    """Reconcile a lead's CRM `Inbox` against where its thread PHYSICALLY
    lives (the inbox whose Gmail actually holds the sent messages / caught
    the reply).

    A thread cannot be moved between two Gmail accounts, so reality wins: if
    the CRM label disagrees with where the mail actually is, the CRM is the
    thing that's wrong and must be corrected to match. This is data repair,
    not routing — stickiness does not apply.

    Returns (needs_change, corrected_label, reason).
    """
    if not is_registered(found_in):
        return (False, current, f"where the thread lives is unknown/unregistered ({found_in!r}); nothing to reconcile")
    if current == found_in:
        return (False, current, f"CRM Inbox already matches reality ({found_in})")
    if not is_registered(current):
        return (True, found_in, f"CRM Inbox was blank/invalid; set to where the thread lives ({found_in})")
    return (True, found_in,
            f"CRM Inbox says {current} but the thread lives in {found_in} — a thread can't move "
            f"between Gmail accounts, so reality wins: correct to {found_in}")
