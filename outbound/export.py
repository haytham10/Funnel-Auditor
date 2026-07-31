"""The upload file, and the preview that is the real gate.

Two outputs:

**`leads.csv`** — one row per lead, carrying an already-assembled `subject` and
`body`. Smartlead stitches nothing. Everything it could get wrong at merge time
is decided here, where it can be linted, and what you read in the preview is
byte-for-byte what leaves. The individual beats ride along as extra columns for
analysis later, but the body is authoritative.

**`preview.txt`** — the emails rendered in full, in order, to be read.

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

# The upload file's columns, in order. `email` first because every tool on
# earth expects it there; `subject` and `body` are what actually send.
COLUMNS = [
    "email", "first_name", "last_name", "full_name", "company",
    "subject", "body",
    "coach_type", "sells_to", "city", "website", "linkedin_url",
    "hook_type", "hook_source_url",
    "identity_line_id", "offer_line_id", "cta_line_id", "ps_line_id",
    "batch", "slug",
]


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

    def row(self, batch: str) -> dict:
        return {
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.name,
            "company": self.company,
            "subject": self.subject,
            "body": self.body,
            "coach_type": self.coach_type,
            "sells_to": self.sells_to,
            "city": self.city,
            "website": self.website,
            "linkedin_url": self.linkedin_url,
            "hook_type": self.hook_type,
            "hook_source_url": self.hook_source_url,
            "identity_line_id": self.anchor_ids.get("identity", ""),
            "offer_line_id": self.anchor_ids.get("offer", ""),
            "cta_line_id": self.anchor_ids.get("cta", ""),
            "ps_line_id": self.anchor_ids.get("ps", ""),
            "batch": batch,
            "slug": self.slug,
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


def write_batch(drafts: list[Draft], lint_results: dict, *,
                out_dir: str | Path = "out", batch: str = "",
                anchor_shares: dict | None = None,
                batch_result=None) -> dict:
    """Write leads.csv and preview.txt for the drafts that passed.

    A lead whose lint failed is not written, and is listed in the report with
    its reasons. A failing batch-level check blocks the whole file, because
    every failure at that level is about the batch as a set — writing "most of
    it" would not fix the thing that failed.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    batch = batch or date.today().isoformat()

    passed, rejected = [], []
    for draft in drafts:
        result = lint_results.get(draft.slug)
        if result is None:
            rejected.append((draft, ["never linted — refusing to write it"]))
        elif not result.passed:
            rejected.append((draft, result.failures))
        else:
            passed.append(draft)

    batch_blocked = bool(batch_result and not batch_result.passed)

    csv_path = out / "leads.csv"
    preview_path = out / "preview.txt"
    rejects_path = out / "rejected.txt"

    if not batch_blocked and passed:
        with open(csv_path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=COLUMNS)
            writer.writeheader()
            for draft in passed:
                writer.writerow(draft.row(batch))
        preview_path.write_text(preview(passed), encoding="utf-8")

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
        lines.append(f"  wrote {csv_path}")
        lines.append(f"  READ {preview_path} BEFORE UPLOADING — it is the gate")

    return {
        "written": len(passed),
        "rejected": len(rejected),
        "blocked": batch_blocked,
        "csv": str(csv_path) if passed and not batch_blocked else "",
        "preview": str(preview_path) if passed and not batch_blocked else "",
        "report": "\n".join(lines),
    }
