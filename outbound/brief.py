"""Where a run has got to, computed from disk instead of remembered.

A batch is one long session today, and that is the single largest line item in
the machine. Measured on `2026-08-03-icf1`: 261.0M tokens, of which **166.5M was
the orchestrator's own context** — 63.8% of the batch and 79.6% of the Opus
bucket, against 40M for both Opus agents combined. `cache_read` is the sum of
the context over every turn, so a run that grows from 30k to 600k over 546 turns
pays for the whole of that growth hundreds of times.

The fix is not a cheaper model and not a weaker check. It is that **the run
should be several short sessions rather than one long one**, each starting near
empty and picking the state up off disk. Nearly everything needed for that is
already written down: `intake`, `dedupe`, `fetch`, `resolve`, `plan`, `select`,
`deal`, `collect`, `redraft` and `export` all leave typed files behind, and
`ledger batch` leaves the label in `work/BATCH` so nobody has to be told it.

What is *not* written down is the residue this module exists for: the headline
numbers each stage printed to the operator and nothing captured. Every flag
`metrics` takes — `--raw`, `--after-dedupe`, `--warm`, `--passed-floors`,
`--tier0-rate`, `--written`, `--rejected`, `--source-list` — is a count an
earlier stage already computed and then dropped on the floor, to be retyped at
the end of a long run from memory. That is not only what makes a `/clear`
unsafe, it is the exact habit the `?`-not-`0` rule was written against.

So this derives what the files can prove and refuses to invent the rest.

**It is an observer and it never fails a run.** Same rule as `ledger` and
`metrics`, and for the same reason: a command that can halt a send file over an
accounting line is a command people learn to route around. Exit 0 when it could
look, exit 2 when it could not — never exit 1, not even when the run is a mess.

**A derived count says what it was derived from; an unknown one prints `?`.**
Nothing here guesses. `warm` is the sharp case: `dedupe` exits 1 on a warm hit
and stops the run, so a `clear.json` on disk *implies* nobody was warm — and
that inference is exactly the kind of reasonable-sounding zero the repo has
twice been burned by. It prints `?` and takes a note instead.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path

NOTES_FILE = "notes.json"

# The keys a note may carry. Closed on purpose: a free-form note file becomes a
# second, unvalidated state store, and the point of this module is to have one
# fewer of those. Each is a number no file on disk can prove.
NOTE_KEYS = {
    "source-list": "what the raw list was called",
    "warm": "warm-thread hits at the early dedupe",
    "copy": "live from Airtable, or cached (deal's COPY: line)",
    "apify-budget": "what `apify limits` said at the top of the batch",
    "chunk": "which chunk of a larger list this batch is",
}

# The run in order: (key, label, the file that proves it ran, what comes next).
# Presence of the file is the whole test. A stage that half-ran leaves a file
# that later checks reject on their own terms; this one only says how far the
# run got, which is the question a fresh session actually has.
STAGES = (
    ("batch", "ledger batch", "BATCH", "python main.py intake <list.csv> --out work/leads.json"),
    ("intake", "intake", "leads.json", "python main.py triage work/leads.json --out work/tiers.json --run-out work/run.json"),
    ("triage", "triage", "tiers.json", "python main.py dedupe work/leads.json --out work/clear.json"),
    ("dedupe", "dedupe (early)", "clear.json", "python main.py fetch work/clear.json --out work/sites.json --with-text"),
    ("fetch", "stage 1 — tier 0", "sites.json", "python main.py resolve work/clear.json --sites work/sites.json --out work/identity.json"),
    ("resolve", "stage 1b — channels", "identity.json", "python main.py email-find --leads work/clear.json --out work/addresses.json --approve-cost"),
    ("addresses", "stage 1bb — addresses", "addresses.json", "python main.py plan work/identity.json --leads work/clear.json --addresses work/addresses.json --out work/plan.json"),
    ("plan", "stage 1c — the ladder", "plan.json", "fan out research-worker, one per slice of ~10"),
    ("research", "stage 2 — research", "researched.json", "python main.py collect draftable --where work"),
    ("draftable", "stage 2 — draftable", "draftable.json", "python main.py copy-check, then deal"),
    ("deal", "stage 2b — the lines", "anchors.json", "python main.py select work/draftable.json --hook-room <lo> --batch <label> --out work/select.json"),
    ("select", "stage 3a — shortlists", "select.json", "fan out hook-worker in waves of six, then hook-verifier"),
    ("hooks", "stage 3b — hooks", "hookverdict", "python main.py collect research --where work --expect work/draftable.json"),
    ("drafts", "stage 4 — drafts", "redraft.json", "python main.py collect drafts --where work --expect work/redraft.json"),
    ("export", "stage 5 — the file", "../out/shipped.json", "read out/preview.txt, then crm-rows and metrics"),
)


@dataclass
class Brief:
    batch: str = ""
    reached: str = ""
    next_command: str = ""
    stages: list = field(default_factory=list)     # (label, present, detail)
    counts: dict = field(default_factory=dict)     # metrics flag -> value or None
    basis: dict = field(default_factory=dict)      # metrics flag -> where it came from
    notes: dict = field(default_factory=dict)
    unreadable: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _load(path: Path):
    """(data, error). A file that will not parse is named, never skipped."""
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except FileNotFoundError:
        return None, None
    except (OSError, ValueError) as exc:
        return None, f"{path.name}: {type(exc).__name__}"


def _count(data) -> int | None:
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        for key in ("leads", "rows", "members", "results"):
            if isinstance(data.get(key), list):
                return len(data[key])
        return 1
    return None


def read_notes(where: str | Path = "work") -> dict:
    data, _ = _load(Path(where) / NOTES_FILE)
    return data if isinstance(data, dict) else {}


def write_note(where: str | Path, key: str, value: str) -> dict:
    """Record one number nothing on disk can prove.

    Rejects an unknown key rather than storing it. The alternative — a note file
    that takes anything — is a second state store with no schema, which is the
    shape of the problem this module was built to remove.
    """
    if key not in NOTE_KEYS:
        raise KeyError(key)
    base = Path(where)
    base.mkdir(parents=True, exist_ok=True)
    notes = read_notes(base)
    notes[key] = value
    (base / NOTES_FILE).write_text(json.dumps(notes, indent=2, sort_keys=True),
                                   encoding="utf-8")
    return notes


def derive(where: str | Path = "work", out: str | Path = "out") -> Brief:
    """Everything the files can prove about where this run has got to."""
    base, outdir = Path(where), Path(out)
    got = Brief()

    label = base / "BATCH"
    if label.exists():
        try:
            got.batch = label.read_text(encoding="utf-8").strip()
        except OSError as exc:
            got.unreadable.append(f"BATCH: {type(exc).__name__}")

    got.notes = read_notes(base)

    # How far the run got. `hookverdict` is a prefix rather than a file because
    # the hook stage writes one per lead and there is no single artifact for it.
    reached_idx = -1
    for idx, (key, human, fname, _) in enumerate(STAGES):
        if fname == "hookverdict":
            hits = sorted(base.glob("hookverdict-*.json"))
            present, detail = bool(hits), f"{len(hits)} verdict(s)"
        elif fname == "BATCH":
            # `work/BATCH` is a label, not JSON. Parsing it as JSON reported an
            # UNREADABLE on every healthy run — an observer crying wolf about
            # its own first check is worse than one that says nothing.
            present, detail = (base / fname).exists(), ""
        else:
            path = base / fname
            present = path.exists()
            data, err = _load(path) if present else (None, None)
            if err:
                got.unreadable.append(err)
            n = _count(data)
            # A dict counts as 1, which is true and useless beside a stage name.
            detail = f"{n}" if isinstance(data, list) else ""
        got.stages.append((human, present, detail))
        if present:
            reached_idx = idx
    if reached_idx >= 0:
        got.reached = STAGES[reached_idx][1]
        got.next_command = STAGES[reached_idx][3]
    else:
        got.reached = "nothing yet"
        got.next_command = STAGES[0][3]

    def _from_file(flag: str, path: Path, how: str):
        data, err = _load(path)
        if err:
            got.unreadable.append(err)
            return
        n = _count(data)
        if n is not None:
            got.counts[flag], got.basis[flag] = n, how

    _from_file("raw", base / "leads.json", "rows in work/leads.json")
    _from_file("after-dedupe", base / "clear.json", "rows in work/clear.json")
    _from_file("passed-floors", base / "draftable.json", "rows in work/draftable.json")
    _from_file("written", outdir / "shipped.json", "rows in out/shipped.json")

    # tier 0: `fetch` already counts the pages it read free. Nobody has published
    # a real number for this niche, and it has been retyped from a printed line
    # into `metrics` by hand on every batch so far.
    sites, err = _load(base / "sites.json")
    if err:
        got.unreadable.append(err)
    elif isinstance(sites, dict) and isinstance(sites.get("ok"), int):
        total = sites.get("total") or _count(sites.get("sites")) or 0
        if total:
            got.counts["tier0-rate"] = round(sites["ok"] / total, 4)
            got.basis["tier0-rate"] = f"{sites['ok']}/{total} read free (work/sites.json)"

    rejected = outdir / "rejected.txt"
    if rejected.exists():
        try:
            lines = [ln for ln in rejected.read_text(encoding="utf-8").splitlines()
                     if ln.strip() and not ln.startswith(" ")]
            got.counts["rejected"], got.basis["rejected"] = len(lines), "out/rejected.txt"
        except OSError as exc:
            got.unreadable.append(f"rejected.txt: {type(exc).__name__}")

    for note_key, flag in (("source-list", "source-list"), ("warm", "warm")):
        if note_key in got.notes:
            got.counts[flag] = got.notes[note_key]
            got.basis[flag] = f"noted at the boundary (`brief --note {note_key}=`)"

    return got


def metrics_command(got: Brief) -> str:
    """The `metrics` call this run has earned, with only what was proved.

    A flag nobody can prove is left OFF rather than passed as 0 — `metrics`
    prints `?` for an absent flag, which is the honest word, and that property
    is worth more than a complete-looking command line.
    """
    parts = ["python main.py metrics work/draftable.json"]
    if got.batch:
        parts.append(f"--batch {got.batch}")
    parts.append("--plan work/plan.json")
    for flag in ("raw", "after-dedupe", "warm", "passed-floors",
                 "tier0-rate", "written", "rejected", "source-list"):
        value = got.counts.get(flag)
        if value is None or value == "":
            continue
        parts.append(f"--{flag} {value}")
    return " \\\n  ".join(parts)


# Which file will prove a flag once its stage has run. The distinction this
# encodes is the useful half of the report: "not measured yet, and here is what
# will measure it" is a different state from "no file can ever prove this, tell
# me if you know it", and printing the same hint for both sent a reader looking
# for a `--note passed-floors` that does not and should not exist.
_PENDING_FROM = {
    "raw": "work/leads.json (intake)",
    "after-dedupe": "work/clear.json (dedupe --stage early)",
    "passed-floors": "work/draftable.json (collect draftable)",
    "tier0-rate": "work/sites.json (fetch)",
    "written": "out/shipped.json (export)",
    "rejected": "out/rejected.txt (export)",
}


def _pending(flag: str) -> str:
    source = _PENDING_FROM.get(flag)
    if source:
        return f"not yet — comes from {source}"
    return f"no file can prove this — `brief --note {flag}=<v>` if you know it"


def report(got: Brief) -> str:
    lines = [f"BRIEF {got.batch or '(no batch label — run `ledger batch`)'}: "
             f"reached {got.reached}"]

    for human, present, detail in got.stages:
        mark = "x" if present else " "
        lines.append(f"  [{mark}] {human}" + (f"   {detail}" if present and detail else ""))

    lines.append("")
    lines.append("  counts for the brief and for `metrics`:")
    for flag in ("raw", "after-dedupe", "warm", "passed-floors",
                 "tier0-rate", "written", "rejected", "source-list"):
        value = got.counts.get(flag)
        shown = "?" if value is None or value == "" else value
        why = got.basis.get(flag) or _pending(flag)
        lines.append(f"    {flag:14} {str(shown):<11} {why}")

    for key, value in sorted(got.notes.items()):
        if key not in ("source-list", "warm"):
            lines.append(f"    note {key:9} {value}")

    for bad in got.unreadable:
        lines.append(f"  UNREADABLE  {bad}")

    lines.append("")
    lines.append(f"  next: {got.next_command}")
    return "\n".join(lines)
