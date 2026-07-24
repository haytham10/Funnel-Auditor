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

          A fresh opener queued AFTER noon Dubai (send_cap.SEND_DAY_CUTOFF_HOUR)
          can't leave today — it is scheduled for tomorrow morning — so it is
          attributed to tomorrow's send-day and gated against tomorrow's ceiling
          using tomorrow's already-scheduled count (`--sends-next-day`), not
          today's already-spent one. Follow-ups and warm replies still go out
          today and are never rolled.

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
logging). The optional DEPTH tag (SHALLOW/DEEP) drives bait-and-reserve:
a shallow finding is self-fixable (worth ~$0 as a sale), a deep finding
needs expertise (worth paying for), and a RESERVED deep finding is the
call bait, held out of email entirely — it is never drawn as a
second-finding (see next_unused_finding):

    1. USED-T1 | SHALLOW | checkout button 404s on mobile
    2. UNUSED | DEEP | pricing split across 4 platforms, buyers bounce at the seam
    3. RESERVED | DEEP | entire program is readable free on the blog

Legacy lines without a DEPTH tag (`N. STATUS | finding`) still parse
(depth = None), so existing rows gate exactly as before.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from audit import inboxes, send_cap

COLD_SEQUENCE_TOUCHES = 3
CARRIERS = ("second-finding", "loom-offer", "disambiguating-question")

# Values that mean "no real verbatim answer was logged".
_ANSWER_PLACEHOLDERS = {
    "", "-", "n/a", "na", "none", "not asked", "not asked yet", "tbd", "pending",
}

_CHECKED = {True, 1, "1", "true", "yes", "checked", "__yes__"}

# `N. STATUS | DEPTH | finding`. STATUS ∈ UNUSED / USED-Tn / RESERVED; the
# DEPTH group (SHALLOW/DEEP) is OPTIONAL so legacy `N. STATUS | finding` rows
# still match (depth → None). Groups: 1=rank, 2=status, 3=depth|None, 4=finding.
_BANK_LINE = re.compile(
    r"^\s*(\d+)\.\s*(UNUSED|USED-T\d|RESERVED)\s*\|\s*(?:(SHALLOW|DEEP)\s*\|\s*)?(\S.*?)\s*$",
    re.IGNORECASE,
)


def _load_row(row_json: str | Path) -> dict:
    return json.loads(Path(row_json).read_text())


def _norm(value) -> str:
    return str(value).strip() if value is not None else ""


def _is_checked(value) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in _CHECKED
    return value in _CHECKED


def parse_findings_bank(value) -> list[dict]:
    """Parse the `Findings Bank` property into [{rank, status, depth, finding}, ...].

    `depth` is "SHALLOW"/"DEEP" when the line carries a depth tag, else None
    (legacy `N. STATUS | finding` rows). `status` is UNUSED / USED-Tn / RESERVED.
    """
    entries = []
    for line in _norm(value).splitlines():
        m = _BANK_LINE.match(line)
        if m:
            depth = m.group(3)
            entries.append({
                "rank": int(m.group(1)),
                "status": m.group(2).upper(),
                "depth": depth.upper() if depth else None,
                "finding": m.group(4),
            })
    return entries


def next_unused_finding(row: dict) -> dict | None:
    """The highest-ranked UNUSED bank entry past #1 (#1 belongs to touch 1).

    Only UNUSED entries are candidates, so a RESERVED deep finding (the call
    bait) is never drawn here — it can never be spent as `--carries
    second-finding`, which is the whole point of reserving it.
    """
    candidates = [e for e in parse_findings_bank(row.get("Findings Bank"))
                  if e["status"] == "UNUSED" and e["rank"] >= 2]
    return min(candidates, key=lambda e: e["rank"]) if candidates else None


def reserved_deep_finding(row: dict) -> dict | None:
    """The deep finding held in reserve as the call bait (RESERVED status), or
    None if the bank holds none. This finding is never emailed — it is the
    reason to get on a call, so the send gate reports it but never spends it."""
    for e in parse_findings_bank(row.get("Findings Bank")):
        if e["status"] == "RESERVED":
            return e
    return None


def opener_finding(row: dict) -> dict | None:
    """The one finding a touch 1 opener must be built from: the lowest-ranked
    UNUSED bank entry (bank #1, chosen depth-first at walk time). Never a
    RESERVED entry — that's the call bait, held out of email entirely.

    Added 2026-07-24 after a real incident: a walk's page-body "strongest
    verified finding" narrative described the same issue the Findings Bank
    correctly tagged `RESERVED | DEEP`, and the draft step built the Touch 1
    email from that narrative instead of the bank's rank order — emailing
    the exact finding the bank was reserving as call bait. `check_send` had
    no way to catch this because nothing cross-checked what the draft
    actually said against the bank. `--opener-rank` closes that gap: the
    draft step must declare which bank rank its email content came from, and
    this function is what it's checked against.
    """
    candidates = [e for e in parse_findings_bank(row.get("Findings Bank"))
                  if e["status"] == "UNUSED"]
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
    now=None,
    sends_next_day: int | None = None,
    opener_rank: int | None = None,
) -> tuple[bool, list[str], list[str]]:
    """Gate for queueing/logging any cold send on this lead.

    sends_today   — TOTAL sends already out of THIS inbox today (all touch
                    types, warm included, both tracks — Gmail sent count).
    touch         — which cold touch this send is (1, 2, or 3).
    followups_due — touch 1 only: follow-ups still owed on the opener's
                    send-day; they eat the budget before any opener does.
    carries       — touch 2/3 only: the new thing this follow-up carries.
    inbox         — which sending inbox this send leaves from; its ceiling
                    is independent (default: the primary inbox). Ignored
                    when cap_state is passed in directly.
    now           — the current moment (default: real Dubai now); used only
                    to decide the opener's send-day (noon Dubai cutoff).
    sends_next_day — touch 1 only, and only relevant PAST the noon Dubai
                    cutoff: the count already attributed to TOMORROW's
                    send-day (tomorrow's already-scheduled sends out of this
                    inbox). A fresh opener queued after noon can't leave
                    today — it is scheduled for tomorrow morning — so it is
                    gated against tomorrow's ceiling using this count, not
                    today's already-spent one. Follow-ups/warm replies are
                    never rolled: they still go out today.
    opener_rank   — touch 1 only, required whenever the Findings Bank is
                    populated: which bank rank the draft's email content was
                    actually built from. Checked against opener_finding()
                    (the lowest-ranked UNUSED entry) — a mismatch, or a rank
                    that turns out to be RESERVED, is a hard fail. Added
                    2026-07-24 after a real incident: a walk's page-body
                    narrative described the same finding the Findings Bank
                    correctly reserved as deep call-bait, and the draft was
                    built from that narrative instead of the bank order,
                    emailing the exact finding the bank was holding back.
                    Nothing previously cross-checked drafted content against
                    the bank, so it passed clean. Legacy rows with no bank
                    at all stay ungated (opener_rank is simply ignored).

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
        # A fresh opener queued after noon Dubai can't leave today — it is
        # scheduled for tomorrow morning — so it is gated against TOMORROW's
        # send-day, using tomorrow's already-scheduled count, never today's
        # already-spent one. Before noon it behaves exactly as before.
        after = send_cap.is_after_send_cutoff(now)
        sday = send_cap.send_day(now)
        if after:
            base_count = sends_next_day
            day_phrase = (
                f"send-day {sday} (past {send_cap.SEND_DAY_CUTOFF_HOUR}:00 Dubai — this opener "
                "is scheduled for tomorrow, so it counts against tomorrow's ceiling)"
            )
        else:
            base_count = sends_today
            day_phrase = f"send-day {sday} (today)"

        bank_entries = parse_findings_bank(row.get("Findings Bank"))
        if bank_entries:
            correct = opener_finding(row)
            if opener_rank is None:
                problems.append(
                    "--opener-rank is required for a touch 1 opener when the Findings Bank "
                    "is populated — declare which bank rank the draft's email content was "
                    "built from, so the gate can confirm it isn't the RESERVED deep "
                    "call-bait finding"
                )
            else:
                entry = next((e for e in bank_entries if e["rank"] == opener_rank), None)
                if entry is None:
                    problems.append(
                        f"--opener-rank {opener_rank} does not match any Findings Bank entry"
                    )
                elif entry["status"] == "RESERVED":
                    where = f'bank #{correct["rank"]} instead' if correct else "an UNUSED entry instead"
                    problems.append(
                        f'--opener-rank {opener_rank} is RESERVED ("{entry["finding"]}") — the '
                        f"deep call-bait finding must never be emailed; the opener must draw {where}"
                    )
                elif correct is not None and entry["rank"] != correct["rank"]:
                    problems.append(
                        f'--opener-rank {opener_rank} ("{entry["finding"]}") is not the opener — '
                        f'bank #{correct["rank"]} ("{correct["finding"]}") is the lowest-ranked '
                        "UNUSED entry and is what the draft must be built from"
                    )
                else:
                    notes.append(
                        f'opener draws bank #{entry["rank"]} ({entry["status"]}): '
                        f'"{entry["finding"]}"'
                    )

        if followups_due is None:
            problems.append(
                "--followups-due is required for a touch 1 opener — follow-ups due on the "
                "opener's send-day eat the budget first; count them and hand the number over"
            )
        elif after and base_count is None:
            problems.append(
                f"it is past {send_cap.SEND_DAY_CUTOFF_HOUR}:00 Dubai, so a new opener is "
                f"attributed to tomorrow's send-day ({sday}) — pass --sends-next-day "
                "(tomorrow's already-scheduled sends out of this inbox) so it is gated "
                "against tomorrow's ceiling, not today's already-spent count"
            )
        else:
            total = base_count + followups_due
            if total >= cap:
                problems.append(
                    f"{base_count} already on {day_phrase} + follow-ups due {followups_due} "
                    f"= {total} >= {cap_state.cap_phrase()} — follow-ups eat the budget first; "
                    "this opener rolls to the next send-day"
                )
            else:
                notes.append(
                    f"touch 1 opener → {day_phrase}: {base_count} already + follow-ups due "
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

    # Bait-and-reserve visibility (not a hard gate). The bank should hold at
    # least one DEEP finding, and one deep finding marked RESERVED is the call
    # bait — held out of email entirely. A lead with only shallow findings still
    # sends (a shallow finding earns the reply), it is just flagged low-value:
    # reply-likely, close-unlikely, because the coach self-fixes what she's shown.
    # Silent on legacy rows that carry no depth tags at all (backward compatible).
    bank = parse_findings_bank(row.get("Findings Bank"))
    depths_tagged = any(e["depth"] is not None for e in bank)
    reserved = reserved_deep_finding(row)
    if reserved is not None:
        notes.append(
            f'deep finding held in reserve (call bait, never emailed): "{reserved["finding"]}"'
        )
    elif depths_tagged and not any(e["depth"] == "DEEP" for e in bank):
        notes.append(
            "WARNING low-value: bank has no DEEP finding — reply-likely, close-unlikely; "
            "a shallow finding earns the reply but the coach self-fixes it, so there is "
            "nothing un-self-fixable to reserve as the reason for a call"
        )
    elif depths_tagged:
        notes.append(
            "WARNING a DEEP finding exists but none is marked RESERVED — mark one RESERVED "
            "so the call bait is held out of email instead of given away"
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
    sends_next_day: int | None = None,
    opener_rank: int | None = None,
) -> int:
    if inbox is not None and not inboxes.is_registered(inbox):
        print(
            f"CRM GATE (send): FAIL — {inbox!r} is not a registered inbox "
            f"(known: {', '.join(inboxes.labels())}). Fix the --inbox label or add it "
            "to audit/inboxes.py; refusing to gate against a phantom inbox."
        )
        return 1
    row = _load_row(row_json)
    cap_state = send_cap.load_cap(inbox)
    ok, problems, notes = check_send(
        row, sends_today, touch, followups_due, carries, cap_state=cap_state,
        sends_next_day=sends_next_day, opener_rank=opener_rank,
    )
    name = _norm(row.get("Contact Name")) or "unnamed lead"
    tag = f" [{cap_state.inbox}]"
    if ok:
        print(f"CRM GATE (send){tag}: PASS — {name}: finding verified, email verified, "
              + ", ".join(notes))
        return 0
    print(f"CRM GATE (send){tag}: FAIL — {name}: " + "; ".join(problems))
    return 1
