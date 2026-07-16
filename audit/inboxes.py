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

_BY_LABEL: dict[str, Inbox] = {ib.label: ib for ib in _REGISTRY}
_BY_ADDRESS: dict[str, Inbox] = {ib.address.lower(): ib for ib in _REGISTRY}

# Fail loudly at import if the registry is malformed — one and only one
# primary, unique labels and addresses. These are invariants the rest of the
# system relies on, not runtime conditions to handle gracefully.
_PRIMARIES = [ib for ib in _REGISTRY if ib.is_primary]
assert len(_PRIMARIES) == 1, f"registry must have exactly one primary inbox, found {len(_PRIMARIES)}"
assert len(_BY_LABEL) == len(_REGISTRY), "inbox labels must be unique"
assert len(_BY_ADDRESS) == len(_REGISTRY), "inbox addresses must be unique"

PRIMARY_LABEL: str = _PRIMARIES[0].label


def labels() -> list[str]:
    """All registered inbox labels, in registry order."""
    return [ib.label for ib in _REGISTRY]


def all_inboxes() -> list[Inbox]:
    return list(_REGISTRY)


def is_registered(label: str | None) -> bool:
    return label in _BY_LABEL


def resolve(label: str | None) -> Inbox:
    """The Inbox for a label; the primary when label is None/empty.

    Raises InboxError on an unknown non-empty label — callers that must fail
    closed instead (e.g. the cap loader) should check is_registered first.
    """
    if not label:
        return _BY_LABEL[PRIMARY_LABEL]
    ib = _BY_LABEL.get(label)
    if ib is None:
        raise InboxError(
            f"{label!r} is not a registered inbox. Known: {', '.join(labels())}. "
            "Add it to audit/inboxes.py first."
        )
    return ib


def primary() -> Inbox:
    return _BY_LABEL[PRIMARY_LABEL]


def label_for_address(address: str | None) -> str | None:
    """The logical label behind a raw address, or None if unregistered."""
    if not address:
        return None
    ib = _BY_ADDRESS.get(address.lower())
    return ib.label if ib else None


def choose_inbox(
    current: str | None,
    caps: dict[str, int],
    counts: dict[str, int],
) -> str:
    """The routing rule — which inbox a lead's next send leaves from.

    STICKY per lead: once a lead has a valid registered assignment, it keeps
    it, so an entire thread (opener + follow-ups + the warm exchange) stays
    on one domain — clean for reply threading and for attributing which
    domain earned a reply or a bounce.

    New/unassigned leads go to the inbox with the most remaining headroom
    today (cap − sends so far), ties broken by registry order (primary
    first). That spreads new openers across inboxes as capacity grows,
    with no hardcoded inbox count — add Inbox 3 to the registry and it
    joins the rotation automatically.

    This function is the single knob for routing policy: change it (e.g. to
    fill-primary-first, or track-based) and the whole system follows.

    caps/counts are keyed by label; a missing entry is treated as cap 0 /
    count 0 so an unregistered-or-unfunded inbox is never chosen for new work.
    """
    if is_registered(current):
        return current  # sticky

    best_label = PRIMARY_LABEL
    best_headroom = None
    for label in labels():  # registry order → primary wins ties
        headroom = caps.get(label, 0) - counts.get(label, 0)
        if best_headroom is None or headroom > best_headroom:
            best_headroom = headroom
            best_label = label
    return best_label
