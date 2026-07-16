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

  send  — no send without `Finding Verified` checked, a real `Email` that is
          also `Email Verified` (deliverability confirmed by `email-verify`,
          not just syntax+MX — a bounce burns the one shared domain), and
          headroom under the daily deliverability ceiling. The ceiling is
          TOTAL sends leaving the inbox (openers + follow-ups + warm
          replies, both tracks), read from send_cap.json (audit/send_cap.py;
          ramps 20 → 25 → 30 by hand, fails closed to 20, hard max 30 for
          one inbox). Budget order is fixed: follow-ups due today eat the
          budget first, new openers get what's left — so a touch 1 send
          must also hand over `--followups-due` and passes only if
          sends_today + followups_due stays under the cap.

          The cold sequence is THREE touches (day 0, 3, 9), then Dormant.
          Touches 2 and 3 must each carry something new — `--carries`
          declares it: `second-finding` (checked against the row's
          `Findings Bank` for an UNUSED entry past #1), `loom-offer`, or
          `disambiguating-question`. A bare bump is a wasted send and a
          spam signal; it doesn't pass this gate.

Row JSON: a flat object of Notion property names → values, as fetched.
Checkbox values may arrive as true/false, "__YES__"/"__NO__" (SQL shape),
or "Yes"/"No" — all accepted.

`Findings Bank` property format, one finding per line, ranked strongest
first (written by the walk, statuses flipped only at confirmed-send
logging):

    1. USED-T1 | checkout button 404s on mobile
    2. UNUSED | replay page still shows the March cohort dates
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from audit import send_cap

COLD_SEQUENCE_TOUCHES = 3
CARRIERS = ("second-finding", "loom-offer", "disambiguating-question")

# Values that mean "no real verbatim answer was logged".
_ANSWER_PLACEHOLDERS = {
    "", "-", "n/a", "na", "none", "not asked", "not asked yet", "tbd", "pending",
}

_CHECKED = {True, 1, "1", "true", "yes", "checked", "__yes__"}

_BANK_LINE = re.compile(r"^\s*(\d+)\.\s*(UNUSED|USED-T\d)\s*\|\s*(\S.*?)\s*$", re.IGNORECASE)


def _load_row(row_json: str | Path) -> dict:
    return json.loads(Path(row_json).read_text())


def _norm(value) -> str:
    return str(value).strip() if value is not None else ""


def _is_checked(value) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in _CHECKED
    return value in _CHECKED


def parse_findings_bank(value) -> list[dict]:
    """Parse the `Findings Bank` property into [{rank, status, finding}, ...]."""
    entries = []
    for line in _norm(value).splitlines():
        m = _BANK_LINE.match(line)
        if m:
            entries.append({
                "rank": int(m.group(1)),
                "status": m.group(2).upper(),
                "finding": m.group(3),
            })
    return entries


def next_unused_finding(row: dict) -> dict | None:
    """The highest-ranked UNUSED bank entry past #1 (#1 belongs to touch 1)."""
    candidates = [e for e in parse_findings_bank(row.get("Findings Bank"))
                  if e["status"] == "UNUSED" and e["rank"] >= 2]
    return min(candidates, key=lambda e: e["rank"]) if candidates else None


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


def check_send(
    row: dict,
    sends_today: int,
    touch: int,
    followups_due: int | None = None,
    carries: str | None = None,
    cap_state: send_cap.CapState | None = None,
    inbox: str | None = None,
) -> tuple[bool, list[str], list[str]]:
    """Gate for queueing/logging any cold send on this lead.

    sends_today   — TOTAL sends already out of THIS inbox today (all touch
                    types, warm included, both tracks — Gmail sent count).
    touch         — which cold touch this send is (1, 2, or 3).
    followups_due — touch 1 only: follow-ups still owed today; they eat
                    the budget before any opener does.
    carries       — touch 2/3 only: the new thing this follow-up carries.
    inbox         — which sending inbox this send leaves from; its ceiling
                    is independent (default: the primary inbox). Ignored
                    when cap_state is passed in directly.

    Returns (ok, problems, notes) — notes are PASS-line detail.
    """
    cap_state = cap_state or send_cap.load_cap(inbox)
    cap = cap_state.cap
    problems: list[str] = []
    notes: list[str] = []

    if not _is_checked(row.get("Finding Verified")):
        problems.append(
            "Finding Verified is unchecked — no send without a verified finding; "
            "a thin finding burns the lead and the domain"
        )

    email = _norm(row.get("Email"))
    if "@" not in email:
        problems.append(f'Email = "{email or "unset"}" — no usable address')
    elif not _is_checked(row.get("Email Verified")):
        # A syntactically-fine address is not a deliverable one. `email-check`
        # (syntax + MX) PASSED for two addresses that then hard-bounced at
        # Touch 1, and a bounce burns the one shared domain the whole ramp
        # protects. `Email Verified` is checked only after `email-verify`
        # (Apify/MillionVerifier) prints PASS, or Haytham checks it by hand to
        # accept a catch_all/unknown risk. Fails closed: missing property =
        # unchecked = not sendable.
        problems.append(
            f'Email Verified is unchecked for "{email}" — deliverability was never '
            "confirmed (email-check is syntax+MX only; a bounce burns the domain). Run "
            "`python main.py email-verify <addr>` — it must print PASS before the box is "
            "checked, or Haytham checks it by hand to accept a catch_all/unknown risk"
        )

    if touch < 1 or touch > COLD_SEQUENCE_TOUCHES:
        problems.append(
            f"touch {touch} does not exist — the cold sequence is {COLD_SEQUENCE_TOUCHES} touches "
            "(day 0, 3, 9); after touch 3 with no reply the lead goes Dormant, never a touch 4"
        )
        return False, problems, notes

    if touch == 1:
        if followups_due is None:
            problems.append(
                "--followups-due is required for a touch 1 opener — follow-ups due today "
                "eat the budget first; count them and hand the number over"
            )
        else:
            total = sends_today + followups_due
            if total >= cap:
                problems.append(
                    f"sends today {sends_today} + follow-ups due {followups_due} = {total} "
                    f">= {cap_state.cap_phrase()} — follow-ups eat the budget first; "
                    "this opener rolls to tomorrow"
                )
            else:
                notes.append(
                    f"touch 1 opener, sends today {sends_today} + follow-ups due "
                    f"{followups_due} = {total} < {cap_state.cap_phrase()} "
                    f"(opener headroom {cap - total})"
                )
    else:
        if sends_today >= cap:
            problems.append(
                f"sends today = {sends_today}, {cap_state.cap_phrase()} — deliverability "
                "ceiling reached, queue this for tomorrow"
            )
        if carries not in CARRIERS:
            problems.append(
                f"touch {touch} must declare what new thing it carries "
                f"(--carries {'|'.join(CARRIERS)}) — a bare bump is a wasted send and a spam signal"
            )
        elif carries == "second-finding":
            entry = next_unused_finding(row)
            if entry is None:
                problems.append(
                    "carries second-finding but the Findings Bank has no UNUSED entry past #1 — "
                    "the bank is empty, missing, or spent; carry the loom-offer or the "
                    "disambiguating-question instead (never invent a finding)"
                )
            else:
                notes.append(
                    f'touch {touch} carries second-finding '
                    f'(bank #{entry["rank"]} UNUSED: "{entry["finding"]}"), '
                    f"sends today {sends_today} < {cap_state.cap_phrase()}"
                )
        else:
            notes.append(
                f"touch {touch} carries {carries}, "
                f"sends today {sends_today} < {cap_state.cap_phrase()}"
            )

    return (not problems), problems, notes


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


def print_send(
    row_json: str | Path,
    sends_today: int,
    touch: int,
    followups_due: int | None = None,
    carries: str | None = None,
    inbox: str | None = None,
) -> int:
    row = _load_row(row_json)
    cap_state = send_cap.load_cap(inbox)
    ok, problems, notes = check_send(
        row, sends_today, touch, followups_due, carries, cap_state=cap_state,
    )
    name = _norm(row.get("Contact Name")) or "unnamed lead"
    tag = f" [{cap_state.inbox}]"
    if ok:
        print(f"CRM GATE (send){tag}: PASS — {name}: finding verified, email verified, "
              + ", ".join(notes))
        return 0
    print(f"CRM GATE (send){tag}: FAIL — {name}: " + "; ".join(problems))
    return 1
