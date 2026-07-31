"""The upload file, and the preview that is the real gate.

Two outputs:

**`leads.csv`** — one row per lead, eight columns, carrying an already-assembled
`subject` and `body`. Smartlead stitches nothing. Everything it could get wrong
at merge time is decided here, where it can be linted, and what you read in the
preview is byte-for-byte what leaves.

**`preview.txt`** — the emails rendered in full, in order, to be read.

**`wall-additions.csv`** — the rows to append to `data/contacted-before.csv`
*after* the batch is actually uploaded. Deliberately not appended here: nothing
has been sent at export time, and walling a lead who never received anything
would silently exclude her from every future batch. `main.py wall-add` closes
that loop once the upload has happened.

There is no automated gate that replaces reading the preview. `lint.py` catches
what a machine can catch: an invented number, a lost claim, a jargon word, a
repeated subject. It cannot catch a hook that lands wrong on a specific person,
or a paragraph that technically passes and still reads like a robot wrote it.
Read ten before anything uploads. That instruction has survived every version of
this system because it is the only step that has ever caught those.

`write_batch` refuses to write a lead that failed the lint. Not a warning, not a
flag in a column — the row does not appear in the upload file. A failing email
in a CSV is an email that gets sent by accident.
"""

from __future__ import annotations

import csv
import textwrap
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

# The upload file's columns. Exactly these, in this order, and nothing else.
#
# `email`, `first_name`, `last_name`, `website`, `location` and
# `linkedin_profile` are Smartlead's OWN lead fields and map straight through.
# `subject` and `body` have no native equivalent and arrive as custom fields,
# usable in a campaign step as {{subject}} and {{body}}.
#
# `linkedin_profile`, not `linkedin_url` — checked against Smartlead's API
# reference. The wrong spelling still imports, which is what makes it worth
# pinning: it silently lands as a 41st custom variable instead of populating the
# native LinkedIn column, and nothing in the upload tells you.
#
# Nothing analytical is here on purpose. Coach type, hook citation, which anchor
# lines were drawn, lint output, batch — all of it lives in Airtable, where it
# can be grouped and filtered. Carrying it in the upload file would add eight
# custom fields to the Smartlead campaign that never get used and clutter every
# lead view.
COLUMNS = [
    "email",
    "first_name",
    "last_name",
    "website",
    "linkedin_profile",
    "location",
    "subject",
    "body",
]

# What gets appended to data/contacted-before.csv AFTER the batch is uploaded.
WALL_COLUMNS = ["name", "email", "domain", "warm", "status", "track"]


@dataclass
class Draft:
    """One finished email, ready to be written or rejected."""
    slug: str = ""
    name: str = ""
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    subject: str = ""
    body: str = ""
    beats: dict = field(default_factory=dict)
    anchor_ids: dict = field(default_factory=dict)
    coach_type: str = ""
    sells_to: str = ""
    city: str = ""
    company: str = ""
    website: str = ""
    linkedin_url: str = ""
    hook_type: str = ""
    hook_source_url: str = ""

    def row(self) -> dict:
        """The Smartlead row. Eight columns, nothing analytical."""
        return {
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "website": self.website,
            "linkedin_profile": self.linkedin_url,
            "location": self.city,
            "subject": self.subject,
            "body": self.body,
        }

    def wall_row(self) -> dict:
        """The row that enters `data/contacted-before.csv` once this is sent.

        Not warm: nobody has replied. It flips only when a reply lands, by hand.
        """
        from audit.urls import registrable_domain
        return {
            "name": self.name,
            "email": self.email,
            "domain": registrable_domain(self.website) if self.website else "",
            "warm": "no",
            "status": "Outreach Sent",
            "track": "Outbound",
        }


def assemble_body(beats: dict, *, sign_off: str = "Haytham",
                  greeting_name: str = "") -> str:
    """Join the beats into the body the model's output actually becomes.

    Order is fixed and load-bearing: hook, identity, offer, close, sign-off, ps.
    Changing it changes every email in the campaign.
    """
    parts = []
    if greeting_name:
        parts.append(f"Hey {greeting_name},")
    for beat in ("hook", "identity", "offer", "cta"):
        text = (beats.get(beat) or "").strip()
        if text:
            parts.append(text)
    parts.append(sign_off)
    ps = (beats.get("ps") or "").strip()
    if ps:
        parts.append(ps)
    return "\n\n".join(parts)


def preview(drafts: list[Draft], *, width: int = 78) -> str:
    """The thing to actually read. Full emails, nothing elided."""
    blocks = []
    for index, draft in enumerate(drafts, 1):
        header = f"{index:>3}. {draft.name}  <{draft.email}>"
        meta = (f"     {draft.coach_type or '?'} / "
                f"{draft.sells_to or 'audience unknown'} / "
                f"{draft.city or 'city unknown'}"
                f"   lines: {','.join(draft.anchor_ids.get(b, '?') for b in ('identity', 'offer', 'cta', 'ps'))}")
        body = "\n".join(
            textwrap.fill(para, width=width) if para.strip() else ""
            for para in draft.body.split("\n")
        )
        blocks.append(
            f"{'=' * width}\n{header}\n{meta}\n{'-' * width}\n"
            f"Subject: {draft.subject}\n\n{body}\n"
        )
    return "\n".join(blocks)


def _normalised(text: str) -> str:
    import re
    return re.sub(r"[^a-z0-9 ]", "", (text or "").lower()).strip()


def check_dealt(drafts: list[Draft], dealt: dict,
                bank=None) -> dict[str, list[str]]:
    """Did each draft actually use the lines the batch deal assigned it?

    A mechanical check on an instruction that is otherwise only prose. The
    drafting worker is told to use the lines it is handed; if it runs
    `main.py anchors` itself instead, it gets the SINGLE-LEAD draw rather than
    the dealt one. That silently undoes the batch balancing — the whole reason
    the deal exists — and leaves the CRM record naming a line the reader never
    saw. Neither is visible by reading the email.

    `dealt` is the JSON `main.py deal --out` writes: email -> {beat: {id, line}}.

    Two checks, because the id is self-reported. The first compares the reported
    id against the deal. The second compares the written text against every
    OTHER line in the same beat: re-voicing the assigned line is the whole
    design, so near-matching it proves nothing, but reproducing a different
    line verbatim is unambiguous — the drafter used the wrong line and reported
    the right id, which leaves the usage counts and the CRM row describing an
    email nobody received.
    """
    problems: dict[str, list[str]] = {}
    others: dict[str, dict[str, str]] = {}
    if bank is not None:
        for beat in ("identity", "offer", "cta", "ps"):
            others[beat] = {_normalised(l.line): l.id
                            for l in getattr(bank, beat)}

    for draft in drafts:
        assigned = dealt.get(draft.email)
        if assigned is None:
            problems.setdefault(draft.slug, []).append(
                "not in the batch deal — where did this lead come from?")
            continue
        for beat in ("identity", "offer", "cta", "ps"):
            want = (assigned.get(beat) or {}).get("id", "")
            got = draft.anchor_ids.get(beat, "")
            if want and got and want != got:
                problems.setdefault(draft.slug, []).append(
                    f"{beat} line is {got}, but the deal assigned {want} — "
                    f"the drafter drew its own instead of using the batch's")
                continue

            written = _normalised((draft.beats or {}).get(beat, ""))
            match = others.get(beat, {}).get(written)
            if match and want and match != want:
                problems.setdefault(draft.slug, []).append(
                    f"{beat} reports {want} but the text is {match} verbatim — "
                    f"the reported line and the written line disagree")
    return problems


def write_batch(drafts: list[Draft], lint_results: dict, *,
                out_dir: str | Path = "out", batch: str = "",
                anchor_shares: dict | None = None,
                batch_result=None, dealt: dict | None = None,
                bank=None) -> dict:
    """Write leads.csv and preview.txt for the drafts that passed.

    A lead whose lint failed is not written, and is listed in the report with
    its reasons. A failing batch-level check blocks the whole file, because
    every failure at that level is about the batch as a set — writing "most of
    it" would not fix the thing that failed.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    batch = batch or date.today().isoformat()

    # `is not None`, not truthiness: an empty deal file means "the deal
    # produced nothing", which must reject every draft, not skip the check.
    drift = check_dealt(drafts, dealt, bank) if dealt is not None else {}

    passed, rejected = [], []
    for draft in drafts:
        result = lint_results.get(draft.slug)
        if draft.slug in drift:
            rejected.append((draft, drift[draft.slug]))
        elif result is None:
            rejected.append((draft, ["never linted — refusing to write it"]))
        elif not result.passed:
            rejected.append((draft, result.failures))
        else:
            passed.append(draft)

    batch_blocked = bool(batch_result and not batch_result.passed)

    csv_path = out / "leads.csv"
    preview_path = out / "preview.txt"
    rejects_path = out / "rejected.txt"

    wall_path = out / "wall-additions.csv"
    usage_path = out / "line-usage.csv"

    if not batch_blocked and passed:
        with open(csv_path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=COLUMNS)
            writer.writeheader()
            for draft in passed:
                writer.writerow(draft.row())
        preview_path.write_text(preview(passed), encoding="utf-8")

        # Written but NOT appended to the wall. Nothing has been sent yet —
        # Haytham uploads by hand, and walling a lead who never actually
        # received anything would silently exclude her from every future batch.
        # `main.py wall-add out/wall-additions.csv` closes the loop afterwards.
        with open(wall_path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=WALL_COLUMNS)
            writer.writeheader()
            for draft in passed:
                writer.writerow(draft.wall_row())

        # Which lines actually shipped, for `main.py copy-usage`. Recorded from
        # the written set only: a line that appeared in a rejected draft never
        # reached a reader and must not count as used.
        usage: dict[str, int] = {}
        for draft in passed:
            for line_id in draft.anchor_ids.values():
                if line_id:
                    usage[line_id] = usage.get(line_id, 0) + 1
        with open(usage_path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["line_id", "count"])
            writer.writeheader()
            for line_id, count in sorted(usage.items()):
                writer.writerow({"line_id": line_id, "count": count})

    if rejected:
        rejects_path.write_text(
            "\n\n".join(
                f"{draft.name} <{draft.email}>\n"
                + "\n".join(f"  - {r}" for r in reasons)
                for draft, reasons in rejected
            ),
            encoding="utf-8",
        )

    lines = [
        f"EXPORT {batch}: {len(passed)} written, {len(rejected)} rejected"
    ]
    if batch_blocked:
        lines.append("  BLOCKED  batch-level lint failed, nothing written:")
        for failure in batch_result.failures:
            lines.append(f"    - {failure}")
    for draft, reasons in rejected:
        lines.append(f"  reject  {draft.name}: {reasons[0]}")
    for beat, shares in (anchor_shares or {}).items():
        top = next(iter(shares.items()), None)
        if top:
            lines.append(f"  {beat} top line {top[0]} at {top[1]:.0%}")
    if not batch_blocked and passed:
        lines.append(f"  wrote {csv_path} ({len(COLUMNS)} columns for Smartlead)")
        lines.append(f"  READ {preview_path} BEFORE UPLOADING — it is the gate")
        lines.append(f"  after uploading: python main.py wall-add {wall_path}")
        lines.append(f"                   python main.py copy-usage {usage_path}")

    return {
        "written": len(passed),
        "rejected": len(rejected),
        "blocked": batch_blocked,
        "csv": str(csv_path) if passed and not batch_blocked else "",
        "preview": str(preview_path) if passed and not batch_blocked else "",
        "wall_additions": str(wall_path) if passed and not batch_blocked else "",
        "line_usage": str(usage_path) if passed and not batch_blocked else "",
        "report": "\n".join(lines),
    }
