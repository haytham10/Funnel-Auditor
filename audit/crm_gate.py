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

  Both `offer` and `send` also gate on FRESHNESS, not just existence, of the
  finding being drawn on. Added 2026-07-26 after the Rita Baki case: her
  3,200 AED offer was scoped around a booking-flow leak she had already
  fixed herself between the walk and the quote (docs/journal.md,
  2026-07-21/25) — Ben Pringle's dead thread showed the same failure mode.
  The walk is a snapshot; threads run 5-10 days; Gate 0 selects for coaches
  who are active enough to notice and fix things. Nothing previously
  re-checked a finding between the walk and the send/quote. `Findings Bank`
  lines now carry an optional `verified:YYYY-MM-DD` tag, set at walk time
  and bumped by `refresh-finding` on every re-check:

      1. USED-T1 | SHALLOW | verified:2026-07-20 | checkout button 404s on mobile
      2. UNUSED | DEEP | verified:2026-07-24 | pricing split across 4 platforms
      3. RESERVED | DEEP | verified:2026-07-24 | entire program is readable free

  `check_send` hard-fails when the drawn finding was last verified more than
  `STALE_SEND_DAYS` (3) days ago. A missing `verified:` tag fails the same way
  a missing date would (never verified = can't prove it isn't stale), and a
  `Findings Bank` that has content but yields no parseable line ALSO fails —
  see `parse_findings_bank`. Only a genuinely empty bank stays ungated, same
  precedent as `--opener-rank`.

  `check_offer` no longer carries a freshness ceiling (2026-07-27, The First
  Five) — see the note above `STALE_SEND_DAYS`.

  refresh — `main.py refresh-finding <row.json> --rank N --url <finding-url>
          --baseline-file <file> [--save-baseline-to <file>]` is the cheap
          re-check: a plain single-URL fetch of just that finding's page
          (never a full Playwright/Firecrawl re-walk), diffed against the
          stored evidence. UNCHANGED closes the loop end to end — it
          auto-stamps `verified:` to today and hands back the full new
          `Findings Bank` value (`new_findings_bank`), ready to write to
          Notion verbatim, no hand-edit. CHANGED never auto-stamps — a text
          diff can prove the page is different, it can't prove the specific
          finding is gone (same trust model as `Finding Verified` never
          being self-certified), so a changed page prints the diff and
          waits on a human read (or a fresh vision pass) before anyone
          bumps the date by hand. `--save-baseline-to` writes this run's
          fetch so the NEXT run — due right as this stamp's ceiling
          approaches — has something to diff against and can auto-stamp too.

  log   — the Email Thread Log is the source of truth for what actually
          went out; `Touch #` and `Notes` are a summary of it, not the
          other way around. Added 2026-07-26 after a 24-lead recovery job:
          confirmed-send logging is two separate writes (an `update_content`
          append + an `update_properties` call) that nothing ties together,
          and on 24 rows the property write landed — `Touch #` incremented,
          `Notes` gained a "Sent Touch N ... reconciled by uae-tick" line —
          while the `update_content` append silently didn't, leaving `Touch
          #` claiming sends the log couldn't back up. This gate re-derives
          the touch history from the page body itself (never trusts a
          caller's count) and fails closed on any gap: `Touch #` = N but the
          log's touch blocks aren't exactly {1, ..., N}. A `Touch #N
          attempt ... BOUNCED` line does not count as touch N — the retry
          that actually sends does. Run this immediately after every
          confirmed-send write, on the fresh re-fetch, before moving to the
          next lead; a FAIL means finish the log append now, not next tick.
"""

from __future__ import annotations

import difflib
import json
import re
from datetime import date
from pathlib import Path

from audit import inboxes, send_cap

COLD_SEQUENCE_TOUCHES = 3

# Freshness ceiling for the finding a SEND draws on (2026-07-26, the Rita Baki
# case — see the module docstring). A send can trail the walk by a few days
# (the cold sequence itself runs day 0/3/9).
#
# Do not loosen this: the finding is still cited in the opener as the evidence
# the work was actually done, and citing a dead one is what Lisa Hugo and
# William Brown both pushed back on. Under The First Five the openers draw on
# calendar/acquisition state, which goes stale in DAYS, not weeks — this
# ceiling is more load-bearing now, not less.
STALE_SEND_DAYS = 3

# `STALE_OFFER_DAYS` (was 1) was REMOVED 2026-07-27 with The First Five.
# Its whole rationale was "a priced offer quotes work, so the work must still
# need doing" — true when the offer was a 735/2,575 AED funnel fix scoped
# around the finding. The First Five sells booked calls and quotes no work
# against the finding at all, so the ceiling was blocking offers for a reason
# that no longer exists. `check_send` keeps its 3-day ceiling; that is where
# the Rita Baki protection actually lives now. Do not reinstate this without
# an offer that once again prices the finding.

_STALE_FINDING_EXPLANATION = (
    "this is the Rita Baki case (docs/journal.md, 2026-07-21/25): her 3,200 AED "
    "offer was scoped around a booking-flow leak she had already fixed herself "
    "between the walk and the quote. Gate 0 selects for coaches active enough to "
    "notice and fix things, so a snapshot finding goes stale fast — re-run "
    "`python main.py refresh-finding` before trusting it again"
)

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

# `N. STATUS | DEPTH | verified:YYYY-MM-DD | finding`. STATUS ∈ UNUSED /
# USED-Tn / RESERVED; the DEPTH group (SHALLOW/DEEP) and the `verified:` date
# tag are both OPTIONAL, independently, so legacy `N. STATUS | finding` and
# `N. STATUS | DEPTH | finding` rows still match (depth/verified → None).
# Groups: 1=rank, 2=status, 3=depth|None, 4=verified date|None, 5=finding.
_BANK_LINE = re.compile(
    r"^\s*(\d+)\.\s*(UNUSED|USED-T\d|RESERVED)\s*\|\s*(?:(SHALLOW|DEEP)\s*\|\s*)?"
    r"(?:verified:(\d{4}-\d{2}-\d{2})\s*\|\s*)?(\S.*?)\s*$",
    re.IGNORECASE,
)

# A real Email Thread Log touch block header, e.g.:
#   [2026-07-20] — Touch #2 — Subject: "..." — Sent
#   2026-07-25 — Touch #2 (turn-two, warm) — Subject: "..." — Sent
# Deliberately does NOT match a bounced attempt ("Touch #1 attempt ...
# BOUNCED") or a logged duplicate ("... DUPLICATE of Touch #1 ...") — neither
# is a real send, so neither should count toward the touch history. The
# negative lookahead only excludes "attempt" right after the number; a
# retry that actually sent is logged as its own "Touch #N" block and counts.
_TOUCH_BLOCK = re.compile(
    r"^\s*\[?\d{4}-\d{2}-\d{2}\]?\s*[—-]\s*Touch\s*#(\d+)(?!\s*attempt)\b",
    re.IGNORECASE | re.MULTILINE,
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
    """Parse the `Findings Bank` property into
    [{rank, status, depth, verified, finding}, ...].

    `depth` is "SHALLOW"/"DEEP" when the line carries a depth tag, else None
    (legacy `N. STATUS | finding` rows). `status` is UNUSED / USED-Tn / RESERVED.
    `verified` is an ISO date string ("YYYY-MM-DD") when the line carries a
    `verified:` tag, else None (never checked, or a pre-2026-07-26 row).
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
                "verified": m.group(4),
                "finding": m.group(5),
            })
    return entries


def bank_is_unparseable(value) -> bool:
    """True when `Findings Bank` has real content but NOT ONE line parses.

    This is the hole the staleness gate itself fell through (2026-07-27). Both
    `check_send`'s freshness block and the old offer one were guarded by a bare
    `if parse_findings_bank(...)`, so a bank that parsed to nothing was read as
    "legacy row, no bank, nothing to check" and skipped the gate ENTIRELY —
    strictly worse than a missing `verified:` tag, which at least fails loudly.
    Rita Baki's row was in exactly this state (its findings were written in a
    bespoke `N. DEAD (...) | finding` grammar) while carrying a live 3,200 AED
    quote scoped around a finding she had already fixed herself.

    A bank where SOME lines parse and others do not is NOT unparseable, and
    must not be: leaving a killed finding in a non-matching grammar is the
    sanctioned way to hide it from the gate without deleting the evidence
    (docs/journal.md, 2026-07-26). Only "content present, zero entries" is the
    broken state.
    """
    if not _norm(value).strip():
        return False
    return not parse_findings_bank(value)


def bump_verified_date(bank_text: str, rank: int, new_date: str) -> str:
    """Return `bank_text` with rank N's `verified:` tag set to `new_date`.

    Every other line is passed through byte-for-byte — this never touches
    STATUS, DEPTH, or the finding text of any entry, including the one it's
    bumping. Unparseable lines (junk, blank lines) are also passed through
    unchanged. Raises ValueError if `rank` matches no line, so a caller can
    never silently write back a bank that's missing the entry it meant to
    stamp.

    This is what closes the refresh-finding loop (H3c, 2026-07-26): instead
    of a human reading a diff and hand-editing the property, `refresh-finding`
    calls this to produce the exact new `Findings Bank` value — ready to
    write to Notion verbatim — whenever the re-fetched page comes back
    unchanged from the stored baseline.
    """
    lines = bank_text.splitlines()
    out = []
    found = False
    for line in lines:
        m = _BANK_LINE.match(line)
        if m and int(m.group(1)) == rank:
            found = True
            status, depth, finding = m.group(2).upper(), m.group(3), m.group(5)
            parts = [f"{rank}. {status}"]
            if depth:
                parts.append(depth.upper())
            parts.append(f"verified:{new_date}")
            parts.append(finding)
            out.append(" | ".join(parts))
        else:
            out.append(line)
    if not found:
        raise ValueError(f"rank {rank} does not match any Findings Bank line")
    return "\n".join(out)


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


def current_finding(row: dict) -> dict | None:
    """The finding the thread is currently standing on: the most-recently
    spent entry (highest `USED-Tn`), or bank #1 if nothing has been sent yet.

    This is what a priced offer, or a touch 2/3 that doesn't carry a fresh
    second-finding (leak-fix-offer / disambiguating-question), is quoting —
    it's the finding staleness has to be checked against even when no NEW
    bank entry is being drawn this round.
    """
    bank = parse_findings_bank(row.get("Findings Bank"))
    if not bank:
        return None

    def _touch_num(entry: dict) -> int:
        try:
            return int(entry["status"].split("-T", 1)[1])
        except (IndexError, ValueError):
            return 0

    used = [e for e in bank if e["status"].startswith("USED-T")]
    if used:
        return max(used, key=_touch_num)
    return next((e for e in bank if e["rank"] == 1), None)


def check_finding_freshness(
    entry: dict | None, max_days: int, today: date | None = None,
) -> tuple[bool, list[str], list[str]]:
    """Is the bank entry a send/offer is drawing on still fresh enough to
    trust? PASS only when `verified:` is set AND is at most `max_days` old.

    A missing `verified:` tag (never checked, or a pre-2026-07-26 row) fails
    the same way an old date would — "never verified" can't prove the finding
    isn't stale, and this gate exists precisely because nothing was re-checking
    that. `entry=None` (nothing to check — an empty bank, or a `--carries
    second-finding` draw with no UNUSED entry left) also fails: a send/offer
    that draws on a finding must have SOME finding to draw on.
    """
    today = today or send_cap.today()
    if entry is None:
        return False, [
            "no Findings Bank entry to check for freshness — " + _STALE_FINDING_EXPLANATION
        ], []

    raw = entry.get("verified")
    if not raw:
        return False, [
            f'bank #{entry["rank"]} ("{entry["finding"]}") has no `verified:` date — it has '
            f"never been re-checked since the walk. Run `python main.py refresh-finding "
            f"--rank {entry['rank']}` and confirm it still holds before this goes out — "
            + _STALE_FINDING_EXPLANATION
        ], []

    try:
        verified_on = date.fromisoformat(raw)
    except ValueError:
        return False, [
            f'bank #{entry["rank"]} ("{entry["finding"]}") has an unparseable `verified:{raw}` '
            "date — fix the tag (YYYY-MM-DD) or re-run refresh-finding. "
            + _STALE_FINDING_EXPLANATION
        ], []

    age = (today - verified_on).days
    if age > max_days:
        return False, [
            f'bank #{entry["rank"]} ("{entry["finding"]}") was last verified {age} day(s) ago '
            f"({verified_on.isoformat()}) — over the {max_days}-day ceiling. " +
            _STALE_FINDING_EXPLANATION
        ], []

    return True, [], [
        f'bank #{entry["rank"]} verified {age} day(s) ago ({verified_on.isoformat()}, '
        f"<= {max_days}-day ceiling)"
    ]


def _fetch_page_text(url: str, timeout: int = 20) -> str:
    """Plain HTTP GET + visible-text extraction — the "single-URL, cheap"
    fetch behind `refresh-finding` (H3c, 2026-07-26). Deliberately NOT the
    Playwright/Firecrawl stack the real walk uses: this has to be cheap
    enough to run before every send, and most funnel pages don't need JS
    rendering to prove a specific element is still there or gone. A page
    that genuinely needs JS (or sits behind a bot wall) will come back
    looking emptier than it is — that's a false "changed", which just means
    a human looks at the diff, never a false "unchanged" that would
    silently auto-stamp a finding that's actually gone.

    Imported lazily (`requests`/`bs4`) so pure-gate commands (crm-gate,
    send-cap, vision) keep working on machines without them installed —
    same precedent as `audit.crawler` staying out of main.py's top-level
    imports.
    """
    import requests
    from bs4 import BeautifulSoup

    resp = requests.get(
        url, timeout=timeout,
        headers={"User-Agent": "Mozilla/5.0 (compatible; FunnelAuditorRefresh/1.0)"},
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    lines = [ln.strip() for ln in soup.get_text("\n").splitlines()]
    return "\n".join(ln for ln in lines if ln)


def check_refresh_finding(
    row: dict,
    rank: int,
    page_text: str,
    baseline_text: str | None,
    today: str | None = None,
) -> tuple[bool, dict]:
    """The cheap re-check behind `refresh-finding`: one already-fetched page
    (live via `--url`, or a pre-fetched `--page-file`), diffed against the
    stored evidence for one Findings Bank entry.

    Not a full re-walk — just that one finding's page. Closes the loop
    (H3c, 2026-07-26): when the page comes back UNCHANGED from the
    baseline, this computes `new_findings_bank` — the full property value
    with that entry's `verified:` tag bumped to `today`, via
    `bump_verified_date` — ready to write to Notion verbatim, no hand-edit.
    A CHANGED page never gets auto-stamped: this can prove a page is
    byte-different, it cannot prove the specific finding still holds (the
    change could be unrelated copy elsewhere on the page) — that call needs
    eyes on the diff or a fresh vision pass, same trust model as `Finding
    Verified` never being self-certified. No baseline at all (first run) is
    the same as changed: nothing to compare against yet, so no stamp.

    Returns (ok, result). `ok=False` only when `rank` doesn't match any bank
    entry — the caller passed a page to diff against nothing.
    """
    bank_text = _norm(row.get("Findings Bank"))
    entry = next((e for e in parse_findings_bank(bank_text) if e["rank"] == rank), None)
    if entry is None:
        return False, {"error": f"--rank {rank} does not match any Findings Bank entry"}

    today = today or send_cap.today().isoformat()
    result = {
        "rank": rank,
        "finding": entry["finding"],
        "status": entry["status"],
        "previous_verified": entry["verified"],
        "today": today,
        "new_findings_bank": None,
    }
    if baseline_text is None:
        result["changed"] = None
        result["diff"] = []
        result["note"] = (
            "no --baseline-file supplied — this fetch has nothing to diff against yet; "
            "save it (--save-baseline-to) so the NEXT refresh-finding run can auto-stamp"
        )
    else:
        diff = list(difflib.unified_diff(
            baseline_text.splitlines(), page_text.splitlines(), lineterm="", n=0,
        ))
        result["changed"] = bool(diff)
        result["diff"] = diff[:40]
        result["diff_truncated"] = len(diff) > 40
        if result["changed"]:
            result["note"] = (
                "page changed since the stored evidence — read the diff and re-confirm "
                "the finding still holds (a vision pass on a changed screenshot beats a "
                "text diff) before hand-bumping `verified:`; NOT auto-stamped"
            )
        else:
            result["new_findings_bank"] = bump_verified_date(bank_text, rank, today)
            result["note"] = (
                f"page unchanged since the stored evidence — `verified:` auto-stamped to "
                f"{today} in `new_findings_bank`; write that value verbatim to the Findings "
                "Bank property"
            )
    return True, result


def touch_blocks(page_body: str) -> list[int]:
    """Every real touch number logged in the Email Thread Log, in document
    order, duplicates included. A bounced attempt or a logged duplicate send
    doesn't match `_TOUCH_BLOCK` and is correctly excluded — see its comment.
    """
    return [int(n) for n in _TOUCH_BLOCK.findall(page_body)]


def check_log_integrity(row: dict, page_body: str) -> tuple[bool, list[str], list[str]]:
    """Re-derive the touch history from the page body and compare it to
    `Touch #`. The property is a claim; the log is the evidence. PASS only
    when the log's touch blocks are EXACTLY {1, ..., Touch #} — no gaps, no
    duplicates, nothing past the claimed count.

    This never trusts a caller-supplied count (that was the bug: the skill
    that wrote `Touch #` is exactly the actor that might have skipped the
    log append, so asking it to also report the block count would just move
    the same failure mode one level up). It re-parses `page_body` itself.
    """
    problems: list[str] = []
    notes: list[str] = []
    expected = row.get("Touch #")
    expected = int(expected) if expected not in (None, "") else 0

    found = touch_blocks(page_body)
    found_set = set(found)
    expected_set = set(range(1, expected + 1))

    missing = sorted(expected_set - found_set)
    if missing:
        problems.append(
            f"Touch # = {expected} but the Email Thread Log has no block for "
            f"touch {', '.join(str(n) for n in missing)} — recover the sent "
            "email from Gmail and append it before trusting this row's history"
        )

    extra = sorted(n for n in found_set if n > expected)
    if extra:
        problems.append(
            f"the log has a Touch #{max(extra)} block but Touch # is only "
            f"{expected} — the property update didn't keep up with the log, "
            "or a block is mislabeled"
        )

    dupes = sorted({n for n in found if found.count(n) > 1} & expected_set)
    if dupes:
        problems.append(
            f"touch {', '.join(str(n) for n in dupes)} has more than one "
            "logged block within the expected range — check for a duplicate "
            "append or a mislabeled touch number"
        )

    if not problems:
        notes.append(f"log blocks match Touch # exactly: {sorted(found_set) or 'none'}")
    return not problems, problems, notes


def check_offer(row: dict, now=None) -> tuple[bool, list[str], list[str]]:
    """Gate for Reply → Offer Sent (and for drafting any priced Sprint offer).

    The question this answers is NOT "do we know their budget" — it is "have
    they earned the right to be told a number". Two routes earn it: they got
    far enough down the funnel that a price is the obvious next thing (an
    EARNED_STATUSES status), or they literally asked what it costs
    (`Asked For Price`). Either one, and the priced offer is a reply. Neither,
    and it is a cold pitch dressed as an offer.

    `Price Discovery Answer` / `Discovery Anchor` are ADVISORY here — they
    sharpen the number, they no longer license it. They come back as notes.

    There is deliberately NO finding-freshness check here any more (removed
    2026-07-27 — see the note where `STALE_OFFER_DAYS` used to live). The offer
    no longer quotes work scoped around the finding, so there is nothing for a
    stale finding to misprice. `check_send` still enforces `STALE_SEND_DAYS`.

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
    touch         — which touch this send is: 1 is always the cold opener;
                    2/3 are the rest of the cold sequence; 4+ is a WARM
                    touch (a thread that got a reply and kept going — Rita
                    Baki reached Touch 5, Avneet Kohli Touch 6). Every touch
                    >= 2 runs the same follow-up gate (carrier + freshness),
                    cold or warm alike — nothing here is special-cased to
                    "2 or 3 only" (that used to be true only by accident,
                    because an upper-bound check on `touch` rejected
                    anything past 3 before it reached this logic).
    followups_due — touch 1 only: follow-ups still owed on the opener's
                    send-day; they eat the budget before any opener does.
    carries       — touch >= 2: the new thing this follow-up carries,
                    warm bumps included.
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

    if touch < 1:
        problems.append(f"touch {touch} is not a valid touch number (must be >= 1)")
        return False, problems, notes
    # touch > COLD_SEQUENCE_TOUCHES (3) is a WARM touch — a thread that got a
    # reply and kept going (Rita Baki reached Touch 5, Avneet Kohli Touch 6).
    # Until 2026-07-26 this branch was unreachable: an upper bound here
    # rejected any touch past 3 outright, so warm sends never reached the
    # freshness check below (or the "must carry something new" check further
    # down) — exactly the gap the Rita Baki incident fell through. Touch 1
    # is still the only opener; every touch >= 2, cold or warm, now runs the
    # same generic follow-up gate (the `else` branch below already treats
    # them uniformly — it never actually special-cased touch 2/3).

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

    # Freshness of the finding this send draws on (2026-07-26, the Rita Baki
    # case — see the module docstring). Touch 1 draws bank #1 (the opener);
    # any touch >= 2 (cold 2/3 OR warm 4+) carrying second-finding draws the
    # next UNUSED entry; every other touch (leak-fix-offer,
    # disambiguating-question, or an undeclared warm bump) still stands on
    # whatever finding was most recently sent. Legacy rows with no bank at
    # all stay ungated, same precedent as --opener-rank. Checked as of
    # `pause_day`, NOT `send_cap.today(now)` — a post-cutoff touch 1 opener
    # is scheduled for TOMORROW, so its finding must still be fresh as of
    # tomorrow, not merely as of right now (the same date `pause_day` above
    # already computes; reusing it keeps the two checks from disagreeing on
    # which day this send actually leaves).
    #
    # "No bank at all" and "a bank nothing can read" are NOT the same thing:
    # the second one used to fall through this `if` and skip the gate silently
    # (2026-07-27 — see `bank_is_unparseable`). It now fails closed.
    if bank_is_unparseable(row.get("Findings Bank")):
        problems.append(
            "`Findings Bank` has content but not one line parses, so there is no "
            "finding to freshness-check and this send would otherwise skip the gate "
            "entirely. Rewrite the bank to `N. UNUSED|USED-Tn|RESERVED | [DEPTH |] "
            "[verified:YYYY-MM-DD |] finding` — one line per finding. (Killed findings "
            "are deliberately left in a non-matching grammar so the gate ignores them; "
            "that is fine, but at least one LIVE line has to parse.) "
            + _STALE_FINDING_EXPLANATION
        )
    elif parse_findings_bank(row.get("Findings Bank")):
        if touch == 1:
            drawn = opener_finding(row)
        elif normalize_carrier(carries)[0] == "second-finding":
            drawn = next_unused_finding(row)
        else:
            drawn = current_finding(row)
        fresh_ok, fresh_problems, fresh_notes = check_finding_freshness(
            drawn, STALE_SEND_DAYS, today=pause_day
        )
        problems.extend(fresh_problems)
        notes.extend(fresh_notes)

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


def print_refresh_finding(
    row_json: str | Path,
    rank: int,
    url: str | None = None,
    page_file: str | Path | None = None,
    baseline_file: str | Path | None = None,
    save_baseline_to: str | Path | None = None,
) -> int:
    """CLI entry for `refresh-finding`. Exactly one of `url` (live fetch,
    the normal path) or `page_file` (a page fetched some other way — a
    JS-heavy page pulled via Firecrawl instead, or a fixture in a test) is
    required. `save_baseline_to`, if given, always writes the text actually
    used for this run — so the very next refresh-finding run (in 3 days,
    right when this one's `verified:` stamp is about to expire) has a
    baseline to diff against and can auto-stamp instead of just reporting."""
    row = _load_row(row_json)
    if url:
        try:
            page_text = _fetch_page_text(url)
        except Exception as exc:  # noqa: BLE001 — report, never crash the caller
            print(json.dumps({"error": f"could not fetch --url {url!r}: {exc}"}))
            return 1
    elif page_file:
        try:
            page_text = Path(page_file).read_text()
        except OSError as exc:
            print(json.dumps({"error": f"cannot read --page-file {str(page_file)!r}: {exc}"}))
            return 1
    else:
        print(json.dumps({"error": "one of --url or --page-file is required"}))
        return 1

    baseline_text = None
    if baseline_file is not None:
        try:
            baseline_text = Path(baseline_file).read_text()
        except OSError as exc:
            print(json.dumps({"error": f"cannot read --baseline-file {str(baseline_file)!r}: {exc}"}))
            return 1

    ok, result = check_refresh_finding(row, rank, page_text, baseline_text)
    if not ok:
        print(json.dumps(result))
        return 1
    if save_baseline_to is not None:
        Path(save_baseline_to).write_text(page_text)
        result["baseline_saved_to"] = str(save_baseline_to)
    print(json.dumps(result, indent=2))
    return 0


def print_log_integrity(row_json: str | Path, page_body_file: str | Path) -> int:
    row = _load_row(row_json)
    page_body = Path(page_body_file).read_text()
    ok, problems, notes = check_log_integrity(row, page_body)
    name = _norm(row.get("Contact Name")) or "unnamed lead"
    if ok:
        print(f"CRM GATE (log): PASS — {name}: " + ", ".join(notes))
        return 0
    print(f"CRM GATE (log): FAIL — {name}: " + "; ".join(problems))
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
