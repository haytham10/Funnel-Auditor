"""
The daily send ceiling — one number for the whole inbox, ramped by hand.

The ceiling counts TOTAL sends leaving the inbox in a day: cold openers,
cold follow-ups, warm replies, discovery questions, money emails, both
tracks. Deliverability doesn't care what kind of email it was.

State lives in send_cap.json at the repo root:

    {"cap": 20, "set_on": "2026-07-14", "history": [...]}

Rules, enforced here rather than documented somewhere:

  - The only legal values are the ramp steps: 20 → 25 → 30.
  - 30 is the HARD ceiling for one inbox. More volume means more inboxes,
    never a bigger number. There is no step after 30.
  - Raising the cap moves exactly one step, requires at least 7 days at
    the current step, and is Haytham's call — `set` exists so HE can run
    it (or explicitly ask for it). No skill ever raises the cap on its
    own; the tick only surfaces the reminder that a step is eligible.
  - Lowering the cap is allowed any time, to any lower step. Backing off
    never needs permission.
  - FAILS CLOSED: a missing, unreadable, or invalid state file means the
    cap is 20. Never fail open to "no cap".

`crm_gate.check_send` reads the cap through load_cap(); the skills read
it through `python main.py send-cap status` and quote the literal line.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

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

STATE_FILE = Path(__file__).resolve().parent.parent / "send_cap.json"


@dataclass
class CapState:
    cap: int
    set_on: date | None
    valid: bool
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


def _fail_closed(problem: str) -> CapState:
    return CapState(cap=FAIL_CLOSED_CAP, set_on=None, valid=False, problem=problem)


def load_cap(path: str | Path = STATE_FILE) -> CapState:
    path = Path(path)
    if not path.exists():
        return _fail_closed(f"{path.name} not found — the ceiling is 20 until the file exists")
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        return _fail_closed(f"{path.name} unreadable ({e.__class__.__name__}) — failing closed to 20")

    cap = data.get("cap")
    if cap not in RAMP_STEPS:
        return _fail_closed(
            f"cap {cap!r} is not a ramp step {RAMP_STEPS} — failing closed to 20"
        )
    try:
        set_on = date.fromisoformat(str(data.get("set_on")))
    except (TypeError, ValueError):
        return _fail_closed(f"set_on {data.get('set_on')!r} is not an ISO date — failing closed to 20")

    return CapState(cap=cap, set_on=set_on, valid=True)


def status_lines(state: CapState | None = None) -> list[str]:
    state = state or load_cap()
    lines: list[str] = []
    if not state.valid:
        lines.append(
            f"SEND CAP: {state.cap}/day total leaving the inbox — FAILED CLOSED: {state.problem}. "
            f"Fix send_cap.json (python main.py send-cap set {state.cap}) to restore normal state."
        )
        return lines

    days = state.days_at_cap
    lines.append(
        f"SEND CAP: {state.cap}/day total leaving the inbox "
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
            f"Haytham's call, never automatic: python main.py send-cap set {nxt}"
        )
    else:
        eligible = state.set_on + timedelta(days=MIN_DAYS_PER_STEP)
        lines.append(
            f"Next step: {nxt}/day, eligible from {eligible} ({MIN_DAYS_PER_STEP} days at "
            f"{state.cap}) and only if deliverability holds. Haytham's call, never automatic."
        )
    return lines


def set_cap(new_cap: int, path: str | Path = STATE_FILE) -> tuple[bool, list[str]]:
    path = Path(path)
    if new_cap not in RAMP_STEPS:
        msg = f"{new_cap} is not a ramp step — the only legal values are {', '.join(map(str, RAMP_STEPS))}."
        if new_cap > HARD_MAX:
            msg += (f" {HARD_MAX}/day is the hard ceiling for one inbox: "
                    "more volume means more inboxes, never a bigger number.")
        return False, [f"SEND CAP: REFUSED — {msg}"]

    state = load_cap(path)
    history = []
    if path.exists() and state.valid:
        try:
            history = json.loads(path.read_text()).get("history", [])
        except (json.JSONDecodeError, OSError):
            history = []

    if state.valid and new_cap == state.cap:
        return True, [f"SEND CAP: already {state.cap}/day (set {state.set_on}) — nothing to do."]

    if state.valid and new_cap > state.cap:
        if new_cap != state.next_step:
            return False, [
                f"SEND CAP: REFUSED — the ramp moves one step at a time "
                f"({state.cap} → {state.next_step}). No skipping steps."
            ]
        days = state.days_at_cap or 0
        if days < MIN_DAYS_PER_STEP:
            return False, [
                f"SEND CAP: REFUSED — only {days} days at {state.cap}/day; a step needs "
                f"{MIN_DAYS_PER_STEP} days of deliverability actually holding before it earns the next one."
            ]
    elif not state.valid and new_cap > FAIL_CLOSED_CAP:
        return False, [
            f"SEND CAP: REFUSED — state is failed closed ({state.problem}); "
            f"re-establish the file at {FAIL_CLOSED_CAP} first: python main.py send-cap set {FAIL_CLOSED_CAP}"
        ]

    if state.valid:
        history.append({"cap": state.cap, "set_on": str(state.set_on)})
    path.write_text(json.dumps(
        {"cap": new_cap, "set_on": str(today()), "history": history}, indent=2,
    ) + "\n")
    lines = [f"SEND CAP: set to {new_cap}/day on {today()}. Each step is Haytham's call, "
             "gated on deliverability having actually held — never raised by a skill on its own."]
    lines += status_lines(load_cap(path))[1:]
    return True, lines


def print_status() -> int:
    for line in status_lines():
        print(line)
    return 0


def print_set(new_cap: int) -> int:
    ok, lines = set_cap(new_cap)
    for line in lines:
        print(line)
    return 0 if ok else 1
