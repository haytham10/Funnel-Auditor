"""
CRM transition gates — the machine-checkable half of the UAE-track hard rules.

Same trust model as the vision gate (vision_gate.py): a script that can't be
talked past, fed by the skill layer. The skill fetches the lead's row from
Notion FRESH, dumps the properties to a JSON file verbatim, and runs the gate.
The gate validates what it's handed; the skill rule is "fetch fresh, pipe
verbatim, quote the literal output line" — never paraphrase a PASS.

Two gates (docs/uae-track/01-crm-operating-spec.md, hard rules 1-3):

  offer — a lead cannot reach `Offer Sent` (and no priced offer may be
          drafted) without a verbatim `Price Discovery Answer` logged AND a
          `Discovery Anchor` set to something other than "Not asked yet".
          Price discovery happens BEFORE the priced offer. That is the
          entire point of the track.

  send  — no send without `Finding Verified` checked, a real `Email`, and
          headroom under the daily deliverability cap (12-15 cold sends/day,
          hard ceiling 15, one inbox, one domain, no backup).

Row JSON: a flat object of Notion property names → values, as fetched.
Checkbox values may arrive as true/false, "__YES__"/"__NO__" (SQL shape),
or "Yes"/"No" — all accepted.
"""

from __future__ import annotations

import json
from pathlib import Path

DAILY_SEND_CAP = 15

# Values that mean "no real verbatim answer was logged".
_ANSWER_PLACEHOLDERS = {
    "", "-", "n/a", "na", "none", "not asked", "not asked yet", "tbd", "pending",
}

_CHECKED = {True, 1, "1", "true", "yes", "checked", "__yes__"}


def _load_row(row_json: str | Path) -> dict:
    return json.loads(Path(row_json).read_text())


def _norm(value) -> str:
    return str(value).strip() if value is not None else ""


def _is_checked(value) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in _CHECKED
    return value in _CHECKED


def check_offer(row: dict) -> tuple[bool, list[str]]:
    """Gate for Reply/Discovery → Offer Sent (and for drafting any priced offer)."""
    problems: list[str] = []

    answer = _norm(row.get("Price Discovery Answer"))
    if answer.lower() in _ANSWER_PLACEHOLDERS:
        problems.append(
            "Price Discovery Answer is empty or a placeholder — their answer must be "
            "logged VERBATIM before any priced offer"
        )

    anchor = _norm(row.get("Discovery Anchor"))
    if not anchor or anchor == "Not asked yet":
        problems.append(
            f'Discovery Anchor = "{anchor or "unset"}" — must be set from their answer '
            "before any priced offer"
        )

    return (not problems), problems


def check_send(row: dict, sends_today: int, cap: int = DAILY_SEND_CAP) -> tuple[bool, list[str]]:
    """Gate for queueing/logging any cold send on this lead."""
    problems: list[str] = []

    if not _is_checked(row.get("Finding Verified")):
        problems.append(
            "Finding Verified is unchecked — no send without a verified finding; "
            "a thin finding burns the lead and the domain"
        )

    email = _norm(row.get("Email"))
    if "@" not in email:
        problems.append(f'Email = "{email or "unset"}" — no usable address')

    if sends_today >= cap:
        problems.append(
            f"sends today = {sends_today}, daily cap is {cap} — deliverability ceiling "
            "reached, queue this for tomorrow"
        )

    return (not problems), problems


def print_offer(row_json: str | Path) -> int:
    row = _load_row(row_json)
    ok, problems = check_offer(row)
    name = _norm(row.get("Contact Name")) or "unnamed lead"
    if ok:
        answer = _norm(row.get("Price Discovery Answer"))
        anchor = _norm(row.get("Discovery Anchor"))
        print(f'CRM GATE (offer): PASS — {name}: answer logged ({len(answer)} chars), '
              f'anchor "{anchor}"')
        return 0
    print(f"CRM GATE (offer): FAIL — {name}: " + "; ".join(problems))
    return 1


def print_send(row_json: str | Path, sends_today: int) -> int:
    row = _load_row(row_json)
    ok, problems = check_send(row, sends_today)
    name = _norm(row.get("Contact Name")) or "unnamed lead"
    if ok:
        print(f"CRM GATE (send): PASS — {name}: finding verified, email set, "
              f"sends today {sends_today}/{DAILY_SEND_CAP}")
        return 0
    print(f"CRM GATE (send): FAIL — {name}: " + "; ".join(problems))
    return 1
