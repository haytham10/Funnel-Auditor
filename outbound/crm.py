"""The Leads row, built in code so a wrong-source join cannot hide in a script.

`audit/airtable.py` says writes stay narrow and nothing here writes a Lead: that
row lands where a human sees it. That boundary is right and it is untouched —
this module **computes** the rows and writes JSON. A person still performs the
write.

## Why it exists

Twenty rows went into the CRM on `2026-08-01-q1` with **no First Name, Last
Name, Website, LinkedIn or City on any of them**. The rows were built from
`work/researched.json` — the research workers' typed output, which has never
carried the intake identity fields; those live on the normalized `Lead` in
`work/clear.json`. A `if v not in (None, "")` filter dropped every empty key
before the request was built, so there was no error and no warning, just absent
columns.

The check that "verified" it counted Name, Status, Hook Verified and Blockers,
saw 20/20, and reported the push as cross-checked. **Those are four fields
somebody expected to be populated.** A verification that only looks where you
expect to find something is the writer certifying its own work with extra steps,
which is the one thing this machine's chassis exists to prevent.

So two things are mechanical here, and they answer the two halves of that:

- **The join is explicit and fails closed.** A research object with no lead
  behind it is a problem, not a row with blanks in it. That is the defect
  itself: the wrong source produced rows that looked fine.
- **Coverage is reported for every field, not the ones anybody expects.** A
  field that is empty on every row is named whether or not it is required,
  because "nobody has a City" and "the City never got read" print identically
  otherwise. `Instagram 0/20` was correct on that batch and `First Name 0/20`
  was the bug; only a report that shows both lets a reader tell.

## What is required, and why the list is short

`Name`, `Email` and `Status` only. Everything else is legitimately absent for
some real lead: the source CSV carried 11 cities for 20 rows, `Sells To` is
collected from their own words and never inferred, and `Subject`/`Body` exist
only for the leads that shipped. A longer required list would fail closed on
true rows, which teaches people to pass a flag that turns the check off.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from audit.airtable import (EMAIL_STATUSES, HOOK_TYPES, HOOK_VERIFIED,
                            LEAD_STATUSES, SELLS_TO, SOLO)
# `Leads.Coach Type` is mirrored by `research`, not by `airtable` — `doc_check`
# names that pairing, so this reads the one the drift check watches rather than
# adding a third copy.
from outbound.research import COACH_TYPES

# The Leads table's field names, exactly as the CRM spells them. Airtable owns
# them; this mirrors them, and `doc-check` is what catches the mirror going
# stale — the same arrangement as `metrics.BATCH_FIELDS`.
REQUIRED = ("Name", "Email", "Status")

# Which single-selects a value has to be in. A bad value is rejected by Airtable
# at the write, which is AFTER the email is in the upload file — the same reason
# `export.check_crm_enums` exists one field over.
ENUMS = {
    "Status": LEAD_STATUSES,
    "Coach Type": COACH_TYPES,
    "Sells To": SELLS_TO,
    "Solo": SOLO,
    "Email Status": EMAIL_STATUSES,
    "Hook Type": HOOK_TYPES,
    "Hook Verified": HOOK_VERIFIED,
}

FLOOR_LABELS = {"uae_based": "Not UAE-based", "is_coach": "Not a coach",
                "active_recent": "Inactive 30d"}


@dataclass
class CrmBuild:
    """The rows, what could not be built, and what every field actually got."""

    rows: list = field(default_factory=list)
    problems: list = field(default_factory=list)
    coverage: dict = field(default_factory=dict)   # field -> rows carrying it
    batch: str = ""

    @property
    def ok(self) -> bool:
        return not self.problems

    def report(self) -> str:
        total = len(self.rows)
        head = "PASS" if self.ok else f"FAIL ({len(self.problems)})"
        lines = [f"CRM: {head} — {total} row(s) built"]
        if self.batch:
            lines.append(f"  link each row's Batch to the {self.batch} Batches "
                         f"record — it is a linked field, so it is not in the "
                         f"rows and cannot be")
        for problem in self.problems:
            lines.append(f"  FAIL  {problem}")
        # Every field, sorted by how empty it is. The empty ones are the whole
        # point: this report exists because a check that looked only at four
        # populated fields called twenty broken rows verified.
        for name, count in sorted(self.coverage.items(), key=lambda kv: (kv[1], kv[0])):
            mark = "EMPTY" if not count else "     "
            lines.append(f"  {mark} {name:22} {count}/{total}")
        lines.append("  A field at 0 is not automatically wrong — check it "
                     "against the source list before assuming either way. It is "
                     "printed so that nobody has to know to look.")
        return "\n".join(lines)


def _lead_key(row: dict) -> str:
    """Email first, slug second. The same key `fetch` and `resolve` join on."""
    return ((row.get("email") or "").strip().lower()
            or (row.get("slug") or "").strip())


def build(leads: list, researches: list, drafts: list | None = None,
          *, batch: str = "") -> CrmBuild:
    """One Leads row per researched lead, joined to its normalized Lead.

    `leads` are normalized Leads (`work/clear.json`), `researches` are the typed
    research objects (`work/researched.json`), `drafts` are the `export.Draft`s
    that actually shipped. Three sources because the row genuinely spans three:
    identity is intake's, verdicts are research's, and what shipped is export's.
    Guessing that one of them carries all three is the defect this replaces.
    """
    out = CrmBuild(batch=batch)
    # Indexed under BOTH keys, not just the preferred one. A research object's
    # email is not guaranteed to be the one the Lead arrived with: the address
    # is re-checked during research, so a hard bounce gets replaced by a
    # verified one and a lead with no deliverable address ends up carrying no
    # email at all. Either way the email-first key stops matching and the row
    # fails to join, which reads as the missing-identity defect this function
    # exists to catch when it is really just the two sides naming the same
    # person differently. On 2026-08-02-q3 that was two of thirty-four: one
    # whose bounced address was swapped for the site's, one with no address
    # found. The slug is stable across both.
    by_key = {}
    for lead in leads or []:
        for key in ((lead.get("email") or "").strip().lower(),
                    (lead.get("slug") or "").strip()):
            if key:
                by_key.setdefault(key, lead)
    shipped = {}
    for draft in drafts or []:
        data = draft if isinstance(draft, dict) else draft.__dict__
        key = (data.get("email") or "").strip().lower() or (data.get("slug") or "")
        if key:
            shipped[key] = data

    for research in researches or []:
        key = _lead_key(research)
        if not key:
            out.problems.append(
                f"a research object for {research.get('name') or '(no name)'!r} "
                f"carries neither email nor slug, so it cannot be joined to a "
                f"lead — a row built from it would have no identity fields")
            continue
        # Both keys on this side too, for the same reason the index carries
        # both: the email is the better key when it matches and the slug is the
        # only one that survives the address being re-checked.
        lead = (by_key.get(key)
                or by_key.get((research.get("slug") or "").strip()))
        if lead is None:
            # The defect itself. Building the row anyway is what produced 20
            # rows with five empty columns and no error.
            out.problems.append(
                f"{key}: no normalized lead — the identity fields (First Name, "
                f"Last Name, Website, LinkedIn, City) live on the Lead and not "
                f"on the research object, so this row would go in blank")
            continue
        out.rows.append(_row(lead, research, shipped.get(key), batch=batch))

    for row in out.rows:
        for name in REQUIRED:
            if not str(row.get(name) or "").strip():
                out.problems.append(
                    f"{row.get('Email') or row.get('Name') or '?'}: {name} is "
                    f"empty and is required")
        for name, allowed in ENUMS.items():
            value = str(row.get(name) or "").strip()
            if value and value not in allowed:
                out.problems.append(
                    f"{row.get('Email') or '?'}: {name}={value!r} is not one of "
                    f"{'/'.join(allowed)} — Airtable will reject the row")
        # An exported lead has a verified hook by construction: a refuted or
        # inconclusive one is not drafted. So a row carrying a Body and a
        # `Hook Verified` that is not `verified` is not a strange lead, it is
        # the stage 3b write-back never having happened — the verdict lives in
        # an agent and only the orchestrator can put it back on the row.
        #
        # It is the same join this module was written for, one field over. The
        # first one lost First Name to a source that never had it; this one
        # loses the three Hook fields to a source that has them only after a
        # human copies them there, and it is quieter, because `proposed` is a
        # legal value that reads like an answer. `metrics` computes its yield
        # from the same fields and reports `null_hook_rate 100%` on a batch
        # that shipped.
        if str(row.get("Status") or "").strip() == "Exported" \
                and str(row.get("Hook Verified") or "").strip() != "verified":
            out.problems.append(
                f"{row.get('Email') or '?'}: the row is Exported but Hook "
                f"Verified is "
                f"{str(row.get('Hook Verified') or '') or '(empty)'!r} — an "
                f"exported email has a verified hook, so this is the stage 3b "
                f"write-back missing. Put hook_verified / hook_type / "
                f"hook_source_url / observation_id back on the research object "
                f"and re-run; `metrics` reads the same fields")

    names = {name for row in out.rows for name in row}
    out.coverage = {
        name: sum(1 for row in out.rows if _filled(row.get(name)))
        for name in names
    }
    return out


def _filled(value) -> bool:
    if value is None:
        return False
    if isinstance(value, (list, tuple, dict, str)):
        return bool(value if not isinstance(value, str) else value.strip())
    return True


def _row(lead: dict, research: dict, draft: dict | None, *, batch: str) -> dict:
    """One row. Every key is written, including the empty ones.

    Writing empties matters: the push that went wrong filtered them out before
    the request, so a field that should have carried a name and did not was
    indistinguishable from a field nobody meant to send.
    """
    failed = [FLOOR_LABELS[floor] for floor in FLOOR_LABELS
              if (research.get(floor) or "unclear") == "no"]
    blockers = _blockers(research, draft, failed)
    row = {
        "Name": lead.get("name") or research.get("name") or "",
        "First Name": lead.get("first_name") or "",
        "Last Name": lead.get("last_name") or "",
        "Email": research.get("email") or lead.get("email") or "",
        "Email Status": research.get("email_status") or "",
        "Website": lead.get("site_url") or "",
        "LinkedIn": lead.get("linkedin_url") or "",
        "Instagram": lead.get("instagram_url") or "",
        "City": lead.get("city") or "",
        "Status": _status(research, draft, blocked=bool(blockers)),
        "Coach Type": research.get("coach_type") or "",
        "Sells To": research.get("sells_to") or "",
        "Solo": research.get("solo") or "",
        "Qualified": not failed,
        "Failed Floors": failed,
        "Evidence": _evidence(research),
        "Audience Size": research.get("audience_size"),
        "Top Program Price AED": research.get("top_program_price_aed"),
        "Hook Type": research.get("hook_type") or "",
        "Hook Source URL": research.get("hook_source_url") or "",
        "Hook Verified": research.get("hook_verified") or "",
        "Subject": draft.get("subject") if draft else "",
        "Body": draft.get("body") if draft else "",
        "Anchor Lines": _anchor_ids(draft),
        "Blockers": blockers,
        "Notes": _notes(research, draft),
    }
    # On an exported lead the CRM's `Hook` must be the sentence that shipped.
    # Three of five rows on `2026-08-01-q1` carried the verifier-certified
    # proposal here while `Body` carried the drafter's rewrite — a CRM row
    # describing an email nobody received, which is the failure `export
    # --anchors` catches one field over. The certified wording moves to Notes.
    row["Hook"] = (_hook_of(draft) if draft else "") or research.get("hook") or ""
    # `Batch` is deliberately absent. It is a linked-record field, so its value
    # is a Batches record id that does not exist until that row is created —
    # emitting the label here would put a string where Airtable wants a link and
    # fail the write on every row. The label is reported instead.
    return row


def _status(research: dict, draft: dict | None, blocked: bool = False) -> str:
    """One of `LEAD_STATUSES`, derived rather than reported.

    A lead that vanished with no record is worse than a kill you can read, so
    every research object gets a status — including a disqualified one.

    **A row with a Blocker is `Held`.** The field's own description in the base
    says every way a lead can stop short is Held with the reason in Blockers, and
    this function said otherwise: a verified hook and no shipped draft read
    `Drafted`, an address and no hook read `Qualified`. Both describe how far the
    lead GOT, which is right mid-run and wrong in the row that outlives the run —
    `2026-08-03-ig237` would have written `Drafted` for three leads a cold reader
    stopped, and left `Held` unused on the first batch that ever had holds.

    `_blockers` already computes exactly this and nothing else could: it is the
    only thing here that knows the batch is over, because it is only ever asked
    at the end of one. So the two fields are coupled rather than a third source
    of truth being invented.
    """
    if any((research.get(floor) or "unclear") == "no" for floor in FLOOR_LABELS):
        return "Disqualified"
    if draft:
        return "Exported"
    if blocked:
        return "Held"
    if (research.get("hook_verified") or "") == "verified":
        return "Drafted"
    if research.get("email"):
        return "Qualified"
    return "Researching"


def _hook_of(draft: dict) -> str:
    beats = draft.get("beats") or {}
    return (beats.get("hook") or "").strip()


def _anchor_ids(draft: dict | None) -> str:
    if not draft:
        return ""
    ids = draft.get("anchor_ids") or {}
    return ", ".join(f"{beat}={ids[beat]}" for beat in sorted(ids) if ids[beat])


def _evidence(research: dict) -> str:
    """The floors with the source each was settled from.

    A verdict with no source is not a verdict (D5), and this is where that shows
    up for a human rather than only in a schema check.
    """
    parts = []
    for floor in ("uae_based", "is_coach", "active_recent"):
        verdict = research.get(floor) or "unclear"
        source = research.get(f"{floor}_source") or "no source"
        parts.append(f"{floor}: {verdict} ({source})")
    return "\n".join(parts)


def _blockers(research: dict, draft: dict | None, failed: list) -> str:
    """Why this lead has no row in the upload file. Empty when it does."""
    if draft:
        return ""
    if failed:
        return "failed the floors: " + ", ".join(failed)
    verdict = research.get("hook_verified") or "none"
    if verdict != "verified":
        return f"no verified hook (hook_verified={verdict})"
    if not research.get("email"):
        return "no verified address"
    return "held after drafting — see the batch's rejected.txt"


def _notes(research: dict, draft: dict | None) -> str:
    """Provenance, and the certified wording when the shipped hook differs.

    Keeping both is what makes the `Hook` field honest: the row says what the
    reader saw, and nothing about how it was certified is lost.
    """
    parts = list(research.get("notes") or [])
    quote = (research.get("hook_quote") or "").strip()
    if quote:
        cited = f'certified quote: "{quote}"'
        source = research.get("hook_source_url") or ""
        stamped = research.get("hook_date") or ""
        if source or stamped:
            cited += f" — {source} {stamped}".rstrip()
        parts.append(cited)
    proposed = (research.get("hook") or "").strip()
    if draft and proposed and proposed != _hook_of(draft):
        parts.append(f"hook as proposed before drafting: {proposed}")
    return "\n".join(p for p in parts if p)
