"""The state files a stage produces, assembled by code instead of by hand.

Three files in this pipeline were written by no command. `work/researched.json`
is the merge of N research slices; `work/draftable.json` is the survivors of the
floors; `work/drafts.json` is every draft that reached SEND. The skill asks the
orchestrator to write all three, which means each one is serialised out of a
context that is already carrying the parts — and then read back into that same
context as a tool result.

That is the most expensive way to concatenate JSON. It also made the whole run
unresumable: a stage whose output exists only because somebody remembered to
write it down cannot be picked up by anything that was not there.

**Fails closed, and prints coverage rather than a bare PASS.** `crm-rows` is the
precedent and the reason: twenty CRM rows once went in with no First Name, Last
Name, Website, LinkedIn or City on any of them, and the check that passed them
looked at four populated fields and reported 20/20. A count of files found is
not a count of files that should exist, so this prints both and names the
difference.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path

# stage -> (glob, output file, what one member is called)
STAGES = {
    "research": ("research-*.json", "researched.json", "research slice"),
    "draftable": ("research-*.json", "draftable.json", "research object"),
    "drafts": ("draft-*.json", "drafts.json", "draft"),
}


@dataclass
class Collected:
    stage: str = ""
    out: str = ""
    members: list = field(default_factory=list)
    files: list = field(default_factory=list)
    missing: list = field(default_factory=list)
    skipped: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _rows(data) -> list:
    """A slice file may hold one object or an array of them."""
    if isinstance(data, dict):
        return [data]
    return [r for r in data if isinstance(r, dict)] if isinstance(data, list) else []


def collect(where: str | Path, stage: str, *, expect: list | None = None,
            only: list | None = None) -> Collected:
    """Gather one stage's members off disk.

    `expect` is the slug list this stage should produce, when the caller knows
    it — the difference between "found six" and "found six of seventeen" is the
    entire value of the check.
    """
    glob, out_name, _ = STAGES[stage]
    base = Path(where)
    got = Collected(stage=stage, out=str(base / out_name))

    keep = set(only) if only else None
    for path in sorted(base.glob(glob)):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            got.skipped.append(f"{path.name}: {type(exc).__name__}")
            continue
        for row in _rows(data):
            slug = str(row.get("slug") or "").strip()
            if keep is not None and slug not in keep:
                continue
            got.members.append(row)
        got.files.append(str(path))

    if stage == "draftable":
        got.members = [r for r in got.members if r.get("passes_floors")
                       or not r.get("failed_floors")]

    seen = {str(r.get("slug") or "").strip() for r in got.members}
    got.missing = sorted(s for s in (expect or []) if s and s not in seen)
    return got


def write(got: Collected, target: str | Path | None = None) -> Path:
    path = Path(target or got.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(got.members, indent=2, default=str),
                    encoding="utf-8")
    return path


def report(got: Collected) -> str:
    _, _, unit = STAGES[got.stage]
    lines = [
        f"COLLECT {got.stage}: {len(got.members)} {unit}(s) from "
        f"{len(got.files)} file(s)"
        + (f", {len(got.missing)} MISSING" if got.missing else ""),
    ]
    for slug in got.missing:
        lines.append(f"  MISSING  {slug} — expected and not on disk. A stage "
                     f"that quietly collected fewer than it should is the "
                     f"failure `crm-rows` exists about")
    for skip in got.skipped:
        lines.append(f"  UNREADABLE  {skip}")
    if not got.members:
        lines.append("  nothing collected — an empty stage is a stage that did "
                     "not run, not a stage where nothing qualified")
    return "\n".join(lines)


def failed(got: Collected) -> bool:
    """Fails closed: a missing expected member, an unreadable file, or nothing."""
    return bool(got.missing or got.skipped or not got.members)
