"""
CRM transition gates — the machine-checkable half of the UAE-track hard rules.

Same trust model as the vision gate (vision_gate.py): a script that can't be
talked past, fed by the skill layer. The skill fetches the lead's row from
Notion FRESH, dumps the properties to a JSON file verbatim, and runs the gate.
The gate validates what it's handed; the skill rule is "fetch fresh, pipe
verbatim, quote the literal output line" — never paraphrase a PASS.

Two gates (docs/uae-track/01-crm-operating-spec.md, hard rules 1-3):

  offer — a lead cannot reach `Offer Sent` (and no priced Sprint / Track A /
          Track B offer may be drafted) until they have EARNED the right to be
          told a number. Two routes earn it, either one is enough: their
          `Status` is one of the earned set (`Call Booked`, `Leak Fix Sold`,
          `Leak Fix Delivered`, `Offer Sent`, `Won` — Status is a single select
          and forward progress overwrites, so a has-been-there status still
          counts), or `Asked For Price` is checked because they literally asked
          what it costs. Neither, and a priced email is a cold pitch wearing an
          offer's clothes.

          SCOPE: this gate governs the priced Sprint / Track A / Track B money
          email only. The 500 AED 48-Hour Leak Fix offered at turn-two is
          EXEMPT — it is the rung that earns the right, so gating it would
          deadlock the motion it exists to start.

          `Price Discovery Answer` and `Discovery Anchor` were the old blockers
          and are now ADVISORY: they sharpen the number, they no longer license
          it. Asking a coach what they'd pay was this track's founding premise
          and it has been falsified — 100 touched leads, 3 answers, 3 ×
          `Refused to name`, 0 numbers named (docs/journal.md, 2026-07-24).
          Nobody names a budget to a stranger over email, and the question is
          now asked on the call. The gate reports both fields as notes on PASS:
          a missing verbatim answer means you are pricing blind, and an anchor
          of "Refused to name" is a WARNING, because that is a TRUST signal,
          not a price signal — the offer email leads harder with the guarantee,
          it does not move the price.

  send  — no send without `Finding Verified` checked, a real `Email` that is
          also `Email Verified` (deliverability confirmed by `email-verify`,
          not just syntax+MX — a bounce burns the one shared domain), and
          headroom under the daily deliverability ceiling. Sends are also
          PAUSED every Sunday (Dubai calendar day), every inbox, cold and
          warm alike — checked first, a hard fail ahead of every other
          reason (send_cap.is_pause_day). The ceiling is
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
          `Findings Bank` for an UNUSED entry past #1), `leak-fix-offer`, or
          `disambiguating-question` (`loom-offer` is still accepted as a
          deprecated alias for `leak-fix-offer`). A bare bump is a wasted
          send and a spam signal; it doesn't pass this gate.

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

# Canonical touch 2/3 carriers. `leak-fix-offer` replaced `loom-offer` on
# 2026-07-24, when the turn-two artifact stopped being "want me to record a
# walkthrough" and became the paid 48-Hour Leak Fix. The old label is still
# accepted so in-flight rows, queued follow-ups and the journal's historical
# `--carries loom-offer` invocations keep working.
CARRIERS = ("second-finding", "leak-fix-offer", "disambiguating-question")

# Deprecated carrier label → canonical. Normalised before validation, and the
# caller is told to stop using it. Kept OUT of CARRIERS so `check_send` compares
# against exactly one canonical value and failure messages advertise only the
# current names.
DEPRECATED_CARRIERS = {"loom-offer": "leak-fix-offer"}

# Everything `--carries` accepts, canonical first. main.py mirrors this list.
CARRIER_CHOICES = CARRIERS + tuple(DEPRECATED_CARRIERS)

# Statuses that mean the lead has EARNED the right to be told a number.
# Status is a single select and forward progress OVERWRITES, so a lead at `Won`
# was necessarily at `Offer Sent` first — being AT one of these is the
# has-been-there test.
EARNED_STATUSES = (
    "Call Booked",
    "Leak Fix Sold",
    "Leak Fix Delivered",
    "Offer Sent",
    "Won",
)

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


def normalize_carrier(carries: str | None) -> tuple[str | None, str | None]:
    """Map a `--carries` value to its canonical name.

    Returns (canonical, deprecation_note). `loom-offer` is a DEPRECATED ALIAS
    for `leak-fix-offer`: it still passes the gate, but the caller is told to
    stop using it. An unknown value comes back unchanged so the caller can
    report it verbatim in the failure message.
    """
    if carries in DEPRECATED_CARRIERS:
        canonical = DEPRECATED_CARRIERS[carries]
        return canonical, (
            f'"{carries}" is a DEPRECATED carrier label — it still passes, but the '
            f'turn-two artifact is now the paid Leak Fix; use "{canonical}"'
        )
    return carries, None


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


def check_offer(row: dict) -> tuple[bool, list[str], list[str]]:
    """Gate for Reply → Offer Sent (and for drafting any priced Sprint offer).

    The question this answers is NOT "do we know their budget" — it is "have
    they earned the right to be told a number". Two routes earn it: they got
    far enough down the funnel that a price is the obvious next thing (an
    EARNED_STATUSES status), or they literally asked what it costs
    (`Asked For Price`). Either one, and the priced offer is a reply. Neither,
    and it is a cold pitch dressed as an offer.

    `Price Discovery Answer` / `Discovery Anchor` are ADVISORY here — they
    sharpen the number, they no longer license it. They come back as notes.

    Returns (ok, problems, notes) — same shape as check_send; notes are
    PASS-line detail.
    """
    problems: list[str] = []
    notes: list[str] = []

    status = _norm(row.get("Status"))
    by_status = status in EARNED_STATUSES
    by_ask = _is_checked(row.get("Asked For Price"))

    if by_status:
        notes.append(f'earned by status "{status}"')
    if by_ask:
        notes.append("earned by ask (Asked For Price checked)")

    if not (by_status or by_ask):
        problems.append(
            f'the lead has not earned a number yet: Status = "{status or "unset"}" is '
            f'not one of {", ".join(EARNED_STATUSES)}, and `Asked For Price` is '
            "unchecked. Two routes earn it — get them to an earned status (the paid "
            "Leak Fix or a booked call), or check `Asked For Price` once they have "
            "actually asked what it costs. Naming a price before either is a cold "
            "pitch, not an offer"
        )

    # --- advisory from here down: reported, never blocking --------------------
    answer = _norm(row.get("Price Discovery Answer"))
    if answer.lower() in _ANSWER_PLACEHOLDERS:
        notes.append(
            "no verbatim Price Discovery Answer logged (advisory) — you are pricing "
            "without their number; lead with the guarantees and expect the anchor "
            "objection in the reply"
        )
    else:
        notes.append(f"discovery answer logged ({len(answer)} chars)")

    anchor = _norm(row.get("Discovery Anchor"))
    if anchor == "Refused to name":
        notes.append(
            'WARNING Discovery Anchor "Refused to name" — that is a TRUST signal, not '
            "a price signal: they withheld a number because they do not yet believe "
            "the outcome, not because of the number. Lead the offer email harder with "
            "the Live-or-Free and First Booking guarantees; a discount answers a "
            "question they never asked"
        )
    elif anchor and anchor != "Not asked yet":
        notes.append(f'anchor "{anchor}"')
    else:
        notes.append(f'no Discovery Anchor set ("{anchor or "unset"}", advisory)')

    return (not problems), problems, notes


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

    # Sends are paused every Sunday (Dubai calendar day) — every inbox, every
    # touch type, cold and warm alike. Not a lower ceiling: zero for the day,
    # checked ahead of headroom/carrier/bank so a Sunday send fails on the
    # pause, not on some other coincidental reason. A touch 1 opener checks
    # the day it will actually leave on (post-cutoff, that's tomorrow); touch
    # 2/3 and warm sends are never rolled, so they check today.
    pause_day = send_cap.send_day(now) if touch == 1 else send_cap.today(now)
    if send_cap.is_pause_day(pause_day):
        problems.append(
            f"{pause_day} is a Sunday — sends are paused every Sunday, no exceptions "
            "(cold and warm, every inbox). Queue it for the next non-Sunday send-day instead."
        )

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
        carries, carrier_deprecation = normalize_carrier(carries)
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
                    "the bank is empty, missing, or spent; carry the leak-fix-offer or "
                    "the disambiguating-question instead (never invent a finding)"
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

        # Appended LAST so the carrier note stays notes[0] for callers that
        # read it positionally.
        if carrier_deprecation and carries in CARRIERS:
            notes.append(carrier_deprecation)

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
    ok, problems, notes = check_offer(row)
    name = _norm(row.get("Contact Name")) or "unnamed lead"
    if ok:
        print(f"CRM GATE (offer): PASS — {name}: " + ", ".join(notes))
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
