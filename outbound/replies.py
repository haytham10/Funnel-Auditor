"""Reply data, joined back to the hook that earned it.

Part 8 of docs/proposals/2026-08-01-hook-retrieval.md ends on the one gap no
retrieval architecture closes: **Smartlead owns replies and there is no API key
in this repo**, so nothing here can compute reply rate, meeting rate, or cost
per booked meeting. For an offer sold on a call, that is the metric that matters
most, and listing it without a collection path would be exactly the aspirational
measurement this machine otherwise refuses.

The bridge that works today is manual, and this is it: Haytham exports a replies
CSV from Smartlead and this joins it on `email` to the batch's leads. That makes
`hook_type` and the hook's source rung **testable against reply rate**, which is
the reason `Hook Type` is a select in the CRM in the first place — its own field
description calls it *"a testable variable against reply rate rather than a
detail buried in prose"*. The variable has existed since the beginning. The test
has never been run.

## Why the columns are sniffed rather than declared

Nothing in this repo has ever seen a Smartlead export. A hard-coded column name
would be a guess that fails on first contact and fails *silently* if the guess
happens to match something else. So the header row is searched for a set of
known spellings, and **when nothing matches it says which headers it did see**
and exits 2 rather than reporting a zero reply rate. A zero here would read as
"the campaign did nothing" when the truth is "this could not find the column",
which is the wall's asymmetry in a third costume.

`--replied-column` and `--email-column` override the sniff, so a real export
that spells something a way this does not know is one flag away from working
rather than a code change.

## A filtered export is a real shape, and it is handled

Smartlead can export "all leads with a reply" — a file where every row IS a
reply and there is no status column to read. That is indistinguishable from a
full export whose reply column this failed to find, and guessing between them
would be the difference between a 6% reply rate and a 100% one. So it is not
guessed: `--all-replied` says the file is pre-filtered, and without it a file
with no reply column is an error.

## What this deliberately does not conclude

**One batch cannot settle which hook type replies better.** Three verified hooks
split across three types is three samples, and the difference between 1 of 1 and
0 of 1 is noise wearing a percentage. This prints counts and rates and states the
sample size beside them; it draws no conclusion and ranks nothing. The test is
worth running because it accumulates, not because the first run answers it.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field, asdict

# Header spellings seen across cold-email tools. Matched case-insensitively
# after stripping spaces, underscores and hyphens, so "Lead Email", "lead_email"
# and "leademail" are one candidate rather than three.
EMAIL_HEADERS = (
    "email", "leademail", "emailaddress", "prospectemail", "contactemail",
    "recipient", "recipientemail", "to", "toemail",
)

# Columns that answer "did this person reply?" — a status, a flag, a count, or
# a timestamp. Order matters: a status column is more specific than a timestamp.
REPLIED_HEADERS = (
    "replied", "isreplied", "hasreplied", "replystatus", "leadstatus",
    "status", "eventtype", "replycount", "replies", "repliedat",
    "replytime", "replydate", "lastreplyat",
)

# Values in a status-shaped column that mean a reply happened. Anything else in
# such a column means it did not — including an empty cell, which is the common
# encoding for "no event yet".
REPLIED_VALUES = (
    "replied", "reply", "replies", "responded", "response", "true", "yes",
    "1", "lead_replied", "email_reply", "interested", "meeting_booked",
)

# Statuses that are ordinary and plainly not replies. Listed so they can be
# passed over SILENTLY rather than reported as values this did not recognise.
# Without it every batch flags `SENT` and `OPENED`, and a note that cries wolf
# on every run is a note nobody reads by the third one — which would waste the
# only mechanism for surfacing a spelling that IS a reply.
NOT_REPLIED_VALUES = (
    "sent", "delivered", "opened", "open", "clicked", "click", "bounced",
    "bounce", "unsubscribed", "unsubscribe", "pending", "queued", "scheduled",
    "inprogress", "notsent", "failed", "blocked", "skipped", "completed",
)


class RepliesUnreadable(RuntimeError):
    """The file could not be read, or its columns could not be identified.

    Never raised for "nobody replied" — that is a finding. This is only ever
    "the question could not be asked", which must not report as an answer.
    """


def _key(header: str) -> str:
    return "".join(ch for ch in (header or "").lower()
                   if ch.isalnum())


def find_column(headers: list, candidates: tuple) -> str:
    """The first header matching a known spelling, or "".

    Exact-match on the normalised form before substring, so a file carrying both
    `email` and `email_body` picks the address rather than the body.
    """
    normalised = {_key(h): h for h in headers if h}
    for candidate in candidates:
        if candidate in normalised:
            return normalised[candidate]
    for candidate in candidates:
        for key, original in normalised.items():
            if candidate in key:
                return original
    return ""


# A column whose values are events-in-time rather than words. Any value in one
# of these IS the event; there is no "SENT" to mistake for a reply.
TIMESTAMP_HINTS = ("at", "time", "date", "on")
COUNT_HINTS = ("count", "num", "total")


def column_kind(header: str) -> str:
    """status | timestamp | count — which decides how a cell is read.

    **The distinction is the whole correctness of this module**, and it was got
    wrong first. A timestamp column's arbitrary value means a reply happened. A
    *status* column's arbitrary value is usually `SENT`, `OPENED` or `BOUNCED`,
    and reading those as replies inflates the rate of whichever hook type
    happened to be in front of them. Deciding by the column rather than by the
    value is what tells the two apart.
    """
    key = _key(header)
    if any(key.endswith(h) or f"{h}" == key for h in TIMESTAMP_HINTS):
        return "timestamp"
    if any(h in key for h in COUNT_HINTS):
        return "count"
    return "status"


def is_reply(value: str, kind: str = "status") -> tuple:
    """(replied, unrecognised) for one cell.

    An empty cell is never a reply and an explicit negative is never a reply,
    whatever the column. Beyond that the column's kind decides.

    **An unrecognised value in a status column is NOT a reply, and says so.**
    That direction is deliberate: under-counting understates a campaign, while
    over-counting makes a hook type look good and drives a real decision on a
    word nobody checked. The value is returned so the caller can name it, which
    is how a spelling this does not know reaches the person who can add it
    rather than being silently swallowed either way.
    """
    text = (value or "").strip().lower()
    if not text or text in ("0", "false", "no", "none", "null", "-", "n/a"):
        return False, ""
    if _key(text) in {_key(v) for v in REPLIED_VALUES}:
        return True, ""
    if _key(text) in {_key(v) for v in NOT_REPLIED_VALUES}:
        return False, ""            # ordinary and plainly not a reply
    if kind == "timestamp":
        return True, ""             # a value in a time column IS the event
    if kind == "count":
        try:
            return float(text.replace(",", "")) > 0, ""
        except ValueError:
            return False, text
    return False, text


@dataclass
class Replies:
    """One batch's replies, attributed to what was in front of the reader."""

    batch: str = ""
    sent: int = 0                    # leads matched between the two files
    replied: int = 0
    reply_rate: float | None = None
    unmatched_rows: int = 0          # in the export, not in this batch
    unmatched_leads: int = 0         # in this batch, not in the export
    by_hook_type: dict = field(default_factory=dict)
    by_rung: dict = field(default_factory=dict)
    email_column: str = ""
    replied_column: str = ""
    notes: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _rate(hits: int, total: int) -> float | None:
    return round(hits / total, 3) if total else None


def load_export(text: str, *, email_column: str = "", replied_column: str = "",
                all_replied: bool = False) -> dict:
    """{email -> replied} from a Smartlead CSV, or a readable refusal."""
    try:
        rows = list(csv.DictReader(io.StringIO(text)))
    except csv.Error as exc:
        raise RepliesUnreadable(f"not readable as CSV: {exc}") from exc
    if not rows:
        raise RepliesUnreadable("the export has a header and no rows")

    headers = list(rows[0].keys())
    email_col = email_column or find_column(headers, EMAIL_HEADERS)
    if not email_col:
        raise RepliesUnreadable(
            f"no email column found. Headers seen: {', '.join(headers)}. "
            f"Pass --email-column to name it.")

    replied_col = replied_column or ("" if all_replied
                                     else find_column(headers, REPLIED_HEADERS))
    if not replied_col and not all_replied:
        raise RepliesUnreadable(
            f"no reply column found in: {', '.join(headers)}. Pass "
            f"--replied-column to name it, or --all-replied if this export is "
            f"already filtered to people who replied. Refusing to guess: a "
            f"pre-filtered file and a file with an unrecognised column look "
            f"identical and differ by the whole answer.")

    kind = column_kind(replied_col) if replied_col else "status"
    out, unknown = {}, {}
    for row in rows:
        address = (row.get(email_col) or "").strip().lower()
        if not address:
            continue
        if all_replied:
            replied, odd = True, ""
        else:
            replied, odd = is_reply(row.get(replied_col, ""), kind)
        if odd:
            unknown[odd] = unknown.get(odd, 0) + 1
        # A lead appearing twice replied if either row says so — an export with
        # one line per sequence step is a shape this must not read as two leads.
        out[address] = out.get(address, False) or replied
    if not out:
        raise RepliesUnreadable(
            f"no addresses in column {email_col!r} — {len(rows)} row(s) read")
    return {"replies": out, "email_column": email_col,
            "column_kind": kind, "unknown_values": unknown,
            "replied_column": replied_col or "(pre-filtered export)"}


def join(leads: list, export: dict, *, batch: str = "") -> Replies:
    """Attribute each reply to the hook type and rung that earned it."""
    from outbound.metrics import rung_of

    replies = export["replies"]
    out = Replies(batch=batch, email_column=export["email_column"],
                  replied_column=export["replied_column"])

    seen = set()
    for lead in leads:
        address = (lead.get("email") or lead.get("lead_key") or "").strip().lower()
        if not address or address not in replies:
            out.unmatched_leads += 1
            continue
        seen.add(address)
        out.sent += 1
        replied = bool(replies[address])
        out.replied += int(replied)

        kind = (lead.get("hook_type") or "?").strip().upper() or "?"
        rung = rung_of(lead.get("hook_source_url") or "")
        for bucket, key in ((out.by_hook_type, kind), (out.by_rung, rung)):
            slot = bucket.setdefault(key, {"sent": 0, "replied": 0})
            slot["sent"] += 1
            slot["replied"] += int(replied)

    out.unmatched_rows = len(set(replies) - seen)
    out.reply_rate = _rate(out.replied, out.sent)
    for bucket in (out.by_hook_type, out.by_rung):
        for slot in bucket.values():
            slot["rate"] = _rate(slot["replied"], slot["sent"])

    # Values this did not recognise, counted as NOT replies and named here. If
    # one of these is actually Smartlead's word for a reply, the rate above is
    # low by that many and the fix is one --replied-column away — but only if
    # somebody can see it, which is what this line is for.
    unknown = export.get("unknown_values") or {}
    if unknown:
        shown = ", ".join(f"{v!r} ×{n}" for v, n in
                          sorted(unknown.items(), key=lambda kv: -kv[1])[:6])
        out.notes.append(
            f"{len(unknown)} unrecognised value(s) in the reply column, counted "
            f"as NOT replies: {shown}. If one of those means a reply, the rate "
            f"above is low — add it or pass --replied-column")

    if out.unmatched_rows:
        out.notes.append(
            f"{out.unmatched_rows} row(s) in the export are not in this batch — "
            f"expected if the export covers more than one upload")
    if out.unmatched_leads:
        out.notes.append(
            f"{out.unmatched_leads} lead(s) in this batch are not in the export "
            f"— not yet sent, or a different campaign")
    return out


def report(out: Replies) -> str:
    """The block a skill quotes. States the sample size beside every rate."""
    def pct(value):
        return "?" if value is None else f"{value * 100:.0f}%"

    lines = [
        f"REPLIES {out.batch or 'unlabelled'}: {out.replied} of {out.sent} "
        f"matched lead(s) replied — {pct(out.reply_rate)}",
        f"  columns  email={out.email_column!r}, reply={out.replied_column!r}",
    ]
    for label, bucket in (("by_hook_type", out.by_hook_type),
                          ("by_rung", out.by_rung)):
        if not bucket:
            continue
        lines.append(f"  {label}")
        for key, slot in sorted(bucket.items()):
            lines.append(f"    {key:12} {slot['replied']}/{slot['sent']}  "
                         f"{pct(slot['rate'])}")
    for note in out.notes:
        lines.append(f"  NOTE  {note}")
    lines.append(
        "  NOT A VERDICT. One batch is a handful of samples per bucket, and the "
        "difference between 1 of 1 and 0 of 1 is noise wearing a percentage. "
        "This is worth running because it accumulates, not because it answers.")
    return "\n".join(lines)
