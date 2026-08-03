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

    if stage in ("research", "draftable"):
        got.skipped.extend(merge_hooks(base, got.members))

    if stage == "draftable":
        got.members = [r for r in got.members if r.get("passes_floors")
                       or not r.get("failed_floors")]

    seen = {str(r.get("slug") or "").strip() for r in got.members}
    got.missing = sorted(s for s in (expect or []) if s and s not in seen)
    return got


def _slug_of(row: dict) -> str:
    return str(row.get("slug") or "").strip().lower()


def _match(row_slug: str, file_slug: str) -> bool:
    """Is this verdict about this lead?

    A worker names its own file — `hook-zee.json` for `coach-zee`, `hook-hadi`
    for `abdul-hadi-mazloum` — so the slug in a verdict is a nickname, not the
    lead's key. Containment either way covers that, and ambiguity is refused
    below rather than resolved: **merging a certification onto the wrong lead
    would ship a verified hook about somebody else**, which is the one mistake
    in this file that reaches a reader.
    """
    if not row_slug or not file_slug:
        return False
    return (row_slug == file_slug or file_slug in row_slug
            or row_slug in file_slug)


def merge_hooks(where: Path, rows: list) -> list[str]:
    """Fold `hook-*.json` and `hookverdict-*.json` onto their research objects.

    The skill has said "merge them in one step" since the verifier was given
    `Write`, and nothing did it — so every lead in a verified batch still read
    `hook_verified: proposed`, which is a legal value that looks like an answer.
    `metrics` then computes `hook_yield 0%` and `null_hook_rate 100%` off it, and
    those are measurements rather than `?`, which defeats the `?`-not-`0` rule
    from underneath. Both gates that catch it run after the send file.

    **The verdict is authoritative and the proposal fills in what it does not
    carry** — `hook_type` and `observation_id` live on the worker's proposal, and
    a verdict that never saw the proposal cannot restate them.

    Returns a list of problems, which the caller adds to `skipped` so
    `failed()` is true: an unmatched or ambiguous verdict is a certification
    nobody can place, and it must not pass quietly.
    """
    problems: list[str] = []
    proposals: dict[str, dict] = {}
    for path in sorted(Path(where).glob("hook-*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            problems.append(f"{path.name}: {type(exc).__name__}")
            continue
        key = path.stem[len("hook-"):].lower()
        entries = _rows(data)
        if not entries:
            # An empty proposal IS the answer: the worker looked and wrote no
            # hook. `proposed` is a legal value that reads like a pending one,
            # so a null hook left at the default is counted by `metrics` as a
            # lead nobody got to rather than as the good answer it is.
            for row in rows:
                if _match(_slug_of(row), key):
                    row["hook_verified"], row["hook"] = "none", ""
            continue
        for entry in entries:
            proposals[key] = entry

    for path in sorted(Path(where).glob("hookverdict-*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            problems.append(f"{path.name}: {type(exc).__name__}")
            continue
        for verdict in _rows(data):
            key = path.stem[len("hookverdict-"):].lower()
            file_slug = str(verdict.get("slug") or key).strip().lower()
            hits = [r for r in rows if _match(_slug_of(r), file_slug)]
            if not hits:
                url = str(verdict.get("hook_source_url") or "")
                hits = [r for r in rows if url and any(
                    url.rstrip("/") == str(o.get("url") or "").rstrip("/")
                    for o in r.get("observations") or [])]
            if len(hits) != 1:
                problems.append(
                    f"{path.name}: names slug {file_slug!r}, which matches "
                    f"{len(hits)} research object(s) — a certification nobody "
                    f"can place is never merged")
                continue
            _apply(hits[0], verdict, proposals.get(key, {}))
    return problems


def _apply(row: dict, verdict: dict, proposal: dict) -> None:
    """One lead's six fields, from the verdict first and the proposal after.

    A REFUTED or INCONCLUSIVE verdict writes the status and **not the hook**.
    Keeping the text of a hook an independent reader refused would leave the
    one field a drafter reads populated and the one a gate reads failing.
    """
    status = str(verdict.get("verdict") or "").strip().lower()
    row["hook_verified"] = status or "proposed"
    if status != "verified":
        row["hook"] = ""
        return
    row["hook"] = verdict.get("resolved_hook") or proposal.get("line") or ""
    row["hook_quote"] = verdict.get("quote_found") or proposal.get("quote") or ""
    row["hook_source_url"] = (verdict.get("hook_source_url")
                              or proposal.get("source_url") or "")
    row["hook_date"] = verdict.get("hook_date") or proposal.get("published_at") or ""
    for field_name, source in (("hook_type", "hook_type"),
                               ("observation_id", "observation_id")):
        value = proposal.get(source)
        if value:
            row[field_name] = value


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
