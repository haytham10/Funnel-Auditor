"""
The daily send ceiling — one ramp PER sending inbox, ramped by hand.

The ceiling counts TOTAL sends leaving ONE inbox in a day: cold openers,
cold follow-ups, warm replies, discovery questions, money emails, both
tracks. Deliverability doesn't care what kind of email it was — but it
cares WHICH domain the mail left from. Each inbox is a separate domain
with its own reputation, so each inbox gets its OWN independent ramp, its
own set_on, and its own history. Caps are additive, never pooled: the way
to send more is another inbox, never a bigger number on one — that is the
whole reason a second inbox exists.

State lives in send_cap.json at the repo root, keyed by the LOGICAL inbox
label ("Inbox 1", "Inbox 2", ...) — the same label the CRM's `Inbox`
property and `crm-gate send --inbox` use. The registry (audit/inboxes.py)
maps a label to its real address; this file never needs to know the address.

    {
      "primary": "Inbox 1",
      "inboxes": {
        "Inbox 1": {"cap": 20, "set_on": "2026-07-14", "history": [...]},
        "Inbox 2": {"cap": 20, "set_on": "2026-07-16", "history": [...]}
      }
    }

Two older shapes are still read and migrated on the next write: the legacy
flat shape ({"cap": 20, "set_on": ..., "history": [...]}) is interpreted as
the primary inbox, and an intermediate address-keyed shape is remapped to
labels via the registry — so nothing in flight breaks.

Rules, enforced here rather than documented somewhere (per inbox):

  - The only legal values are the ramp steps: 20 → 25 → 30.
  - 30 is the HARD ceiling for ONE inbox. More volume means more inboxes,
    never a bigger number. There is no step after 30.
  - A new inbox REGISTERS at 20 and ramps from there — you cannot register
    one straight into a higher step.
  - Raising the cap moves exactly one step, requires at least 7 days at
    the current step, and is Haytham's call — `set` exists so HE can run
    it (or explicitly ask for it). No skill ever raises the cap on its
    own; the tick only surfaces the reminder that a step is eligible.
  - Lowering the cap is allowed any time, to any lower step. Backing off
    never needs permission.
  - FAILS CLOSED, per inbox: a missing, unreadable, or invalid state file,
    OR an inbox that is not registered, means the cap is 20 for that
    inbox. Never fail open to "no cap".

`crm_gate.check_send` reads the cap through load_cap(inbox); the skills
read it through `python main.py send-cap status [--inbox ...]` and quote
the literal line.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from audit import inboxes

# The send-day is the DUBAI calendar day (UTC+4, no DST), everywhere: the
# inbox's audience lives there, the tick fires at 02:53 UTC (06:53 Dubai),
# and mixing server-local, UTC, and Gmail-account days put up to 4 hours of
# disagreement exactly inside the window the tick runs in. Anything that
# counts or dates sends uses this, never date.today().
DUBAI_TZ = timezone(timedelta(hours=4))


def today() -> date:
    """Today's date in Dubai — the canonical send-day for the whole system."""
    return datetime.now(DUBAI_TZ).date()


RAMP_STEPS = (20, 25, 30)
HARD_MAX = 30
FAIL_CLOSED_CAP = 20
MIN_DAYS_PER_STEP = 7

# The default inbox when nothing selects one — the registry's primary
# ("Inbox 1"). The legacy flat state file, and the intermediate
# address-keyed shape, are both migrated onto logical labels on read (see
# _normalize), so every existing caller keeps its exact behavior.
PRIMARY_INBOX = inboxes.PRIMARY_LABEL

STATE_FILE = Path(__file__).resolve().parent.parent / "send_cap.json"


@dataclass
class CapState:
    cap: int
    set_on: date | None
    valid: bool
    inbox: str = PRIMARY_INBOX
    registered: bool = True  # False if this inbox has no entry in the state file
    problem: str = ""  # why we failed closed, if we did

    @property
    def days_at_cap(self) -> int | None:
        if self.set_on is None:
            return None
        return (today() - self.set_on).days

    @property
    def step_index(self) -> int:
        return RAMP_STEPS.index(self.cap)

    @property
    def next_step(self) -> int | None:
        i = self.step_index
        return RAMP_STEPS[i + 1] if i + 1 < len(RAMP_STEPS) else None

    def cap_phrase(self) -> str:
        """Short provenance phrase for gate output lines."""
        if not self.valid:
            return f"cap {self.cap} (FAILED CLOSED: {self.problem})"
        return f"cap {self.cap}"


def _fail_closed(inbox: str, problem: str, registered: bool = True) -> CapState:
    return CapState(
        cap=FAIL_CLOSED_CAP, set_on=None, valid=False,
        inbox=inbox, registered=registered, problem=problem,
    )


def _relabel_key(key: str) -> str:
    """Map a stored inbox key onto a logical label.

    Keys are logical labels ("Inbox 1"). An intermediate version of this
    file was keyed by raw address ("haytham@auto-mate.one") — those are
    remapped to their label via the registry so that old file still loads.
    An unrecognized key is left as-is (it will fail closed on read).
    """
    if inboxes.is_registered(key):
        return key
    return inboxes.label_for_address(key) or key


def _normalize(data) -> dict:
    """Return the state as the keyed shape {"primary": ..., "inboxes": {...}}.

    Accepts the label-keyed shape, the intermediate address-keyed shape
    (remapped to labels), or the legacy flat shape (read as the primary
    inbox). Anything unrecognizable becomes an empty registry — every inbox
    then fails closed on read, which is the safe direction.
    """
    if not isinstance(data, dict):
        return {"primary": PRIMARY_INBOX, "inboxes": {}}
    stored = data.get("inboxes")
    if isinstance(stored, dict):
        remapped = {_relabel_key(k): v for k, v in stored.items()}
        primary = _relabel_key(data.get("primary") or PRIMARY_INBOX)
        return {"primary": primary, "inboxes": remapped}
    if "cap" in data:  # legacy flat shape → the primary inbox
        return {
            "primary": PRIMARY_INBOX,
            "inboxes": {PRIMARY_INBOX: {
                "cap": data.get("cap"),
                "set_on": data.get("set_on"),
                "history": data.get("history", []),
            }},
        }
    return {"primary": PRIMARY_INBOX, "inboxes": {}}


def _read_state(path: str | Path) -> dict:
    """Normalized state dict, tolerating a missing or unreadable file."""
    path = Path(path)
    if not path.exists():
        return {"primary": PRIMARY_INBOX, "inboxes": {}}
    try:
        return _normalize(json.loads(path.read_text()))
    except (json.JSONDecodeError, OSError):
        return {"primary": PRIMARY_INBOX, "inboxes": {}}


def load_cap(inbox: str | None = None, path: str | Path = STATE_FILE) -> CapState:
    inbox = inbox or PRIMARY_INBOX
    path = Path(path)
    if not path.exists():
        return _fail_closed(
            inbox, f"{path.name} not found — the ceiling is {FAIL_CLOSED_CAP} until the file exists",
            registered=False,
        )
    try:
        raw = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        return _fail_closed(
            inbox, f"{path.name} unreadable ({e.__class__.__name__}) — failing closed to {FAIL_CLOSED_CAP}",
            registered=False,
        )

    entry = _normalize(raw)["inboxes"].get(inbox)
    if entry is None:
        return _fail_closed(
            inbox,
            f"inbox {inbox!r} is not registered in {path.name} — failing closed to {FAIL_CLOSED_CAP}",
            registered=False,
        )

    cap = entry.get("cap")
    if cap not in RAMP_STEPS:
        return _fail_closed(inbox, f"cap {cap!r} is not a ramp step {RAMP_STEPS} — failing closed to {FAIL_CLOSED_CAP}")
    try:
        set_on = date.fromisoformat(str(entry.get("set_on")))
    except (TypeError, ValueError):
        return _fail_closed(inbox, f"set_on {entry.get('set_on')!r} is not an ISO date — failing closed to {FAIL_CLOSED_CAP}")

    return CapState(cap=cap, set_on=set_on, valid=True, inbox=inbox)


def load_all(path: str | Path = STATE_FILE) -> dict[str, CapState]:
    """Every registered inbox → its CapState, in file order."""
    state = _read_state(path)
    return {name: load_cap(name, path) for name in state["inboxes"]}


def status_lines(state: CapState | None = None, inbox: str | None = None) -> list[str]:
    state = state or load_cap(inbox)
    label = state.inbox
    lines: list[str] = []
    if not state.valid:
        lines.append(
            f"SEND CAP [{label}]: {state.cap}/day total leaving the inbox — FAILED CLOSED: {state.problem}. "
            f"Fix send_cap.json (python main.py send-cap set {state.cap} --inbox {label}) to restore normal state."
        )
        return lines

    days = state.days_at_cap
    lines.append(
        f"SEND CAP [{label}]: {state.cap}/day total leaving the inbox "
        f"(ramp step {state.step_index + 1} of {len(RAMP_STEPS)}, set {state.set_on}, "
        f"day {days} at this step)"
    )
    nxt = state.next_step
    if nxt is None:
        lines.append(
            f"{HARD_MAX}/day is the hard ceiling for one inbox. "
            "More volume means more inboxes, never a bigger number."
        )
    elif days is not None and days >= MIN_DAYS_PER_STEP:
        lines.append(
            f"RAMP REMINDER: {state.cap}/day has held for {days} days. If deliverability held "
            f"(no bounces, no spam-folder hits, reply rate steady), the next step is {nxt}/day. "
            f"Haytham's call, never automatic: python main.py send-cap set {nxt} --inbox {label}"
        )
    else:
        eligible = state.set_on + timedelta(days=MIN_DAYS_PER_STEP)
        lines.append(
            f"Next step: {nxt}/day, eligible from {eligible} ({MIN_DAYS_PER_STEP} days at "
            f"{state.cap}) and only if deliverability holds. Haytham's call, never automatic."
        )
    return lines


def all_status_lines(path: str | Path = STATE_FILE) -> list[str]:
    caps = load_all(path)
    if not caps:
        return [
            f"SEND CAP: no inboxes registered in {Path(path).name} — every send fails closed "
            f"to {FAIL_CLOSED_CAP}/day. Register one: python main.py send-cap set {FAIL_CLOSED_CAP} --inbox <address>"
        ]
    lines: list[str] = []
    total = 0
    for st in caps.values():
        lines += status_lines(st)
        total += st.cap
        lines.append("")
    lines.append(
        f"TOTAL system ceiling: {total}/day across {len(caps)} inbox(es) — "
        "independent ramps, additive capacity."
    )
    return lines


def set_cap(new_cap: int, inbox: str | None = None, path: str | Path = STATE_FILE) -> tuple[bool, list[str]]:
    inbox = inbox or PRIMARY_INBOX
    path = Path(path)

    if not inboxes.is_registered(inbox):
        return False, [
            f"SEND CAP [{inbox}]: REFUSED — not a registered inbox "
            f"(known: {', '.join(inboxes.labels())}). Add it to audit/inboxes.py "
            "before giving it a ceiling — the registry is the source of truth."
        ]

    if new_cap not in RAMP_STEPS:
        msg = f"{new_cap} is not a ramp step — the only legal values are {', '.join(map(str, RAMP_STEPS))}."
        if new_cap > HARD_MAX:
            msg += (f" {HARD_MAX}/day is the hard ceiling for one inbox: "
                    "more volume means more inboxes, never a bigger number.")
        return False, [f"SEND CAP [{inbox}]: REFUSED — {msg}"]

    state = load_cap(inbox, path)
    all_state = _read_state(path)
    entry = all_state["inboxes"].get(inbox)
    was_registered = entry is not None
    history = list(entry.get("history", [])) if entry else []

    # Corrupt-but-registered, or not-registered-at-all: the only legal write
    # is the base cap, which re-establishes / registers the inbox. Never fail
    # open to a higher cap off a broken or absent state.
    if not state.valid:
        if new_cap > FAIL_CLOSED_CAP:
            if was_registered:
                return False, [
                    f"SEND CAP [{inbox}]: REFUSED — state is failed closed ({state.problem}); "
                    f"re-establish at {FAIL_CLOSED_CAP} first: python main.py send-cap set {FAIL_CLOSED_CAP} --inbox {inbox}"
                ]
            return False, [
                f"SEND CAP [{inbox}]: REFUSED — a new inbox registers at {FAIL_CLOSED_CAP}/day and ramps "
                f"from there: python main.py send-cap set {FAIL_CLOSED_CAP} --inbox {inbox}"
            ]
        all_state["inboxes"][inbox] = {"cap": new_cap, "set_on": str(today()), "history": history}
        all_state.setdefault("primary", PRIMARY_INBOX)
        path.write_text(json.dumps(all_state, indent=2) + "\n")
        verb = "re-established at" if was_registered else "registered at"
        lines = [f"SEND CAP [{inbox}]: {verb} {new_cap}/day on {today()}."]
        lines += status_lines(load_cap(inbox, path))[1:]
        return True, lines

    # Valid existing state.
    if new_cap == state.cap:
        return True, [f"SEND CAP [{inbox}]: already {state.cap}/day (set {state.set_on}) — nothing to do."]

    if new_cap > state.cap:
        if new_cap != state.next_step:
            return False, [
                f"SEND CAP [{inbox}]: REFUSED — the ramp moves one step at a time "
                f"({state.cap} → {state.next_step}). No skipping steps."
            ]
        days = state.days_at_cap or 0
        if days < MIN_DAYS_PER_STEP:
            return False, [
                f"SEND CAP [{inbox}]: REFUSED — only {days} days at {state.cap}/day; a step needs "
                f"{MIN_DAYS_PER_STEP} days of deliverability actually holding before it earns the next one."
            ]
    # (lowering is always allowed, no further checks)

    history.append({"cap": state.cap, "set_on": str(state.set_on)})
    all_state["inboxes"][inbox] = {"cap": new_cap, "set_on": str(today()), "history": history}
    all_state.setdefault("primary", PRIMARY_INBOX)
    path.write_text(json.dumps(all_state, indent=2) + "\n")
    lines = [f"SEND CAP [{inbox}]: set to {new_cap}/day on {today()}. Each step is Haytham's call, "
             "gated on deliverability having actually held — never raised by a skill on its own."]
    lines += status_lines(load_cap(inbox, path))[1:]
    return True, lines


def print_status(inbox: str | None = None, show_all: bool = False) -> int:
    lines = all_status_lines() if show_all else status_lines(inbox=inbox)
    for line in lines:
        print(line)
    return 0


def print_set(new_cap: int, inbox: str | None = None) -> int:
    ok, lines = set_cap(new_cap, inbox=inbox)
    for line in lines:
        print(line)
    return 0 if ok else 1
