"""The retrieval ledger: one JSON line per fetch, written as the run proceeds.

Every cost claim ever made about this machine was reconstructed by hand from a
journal entry. The first real batch could not answer *which rung produced our
hooks* or *what did the leads that produced nothing cost us*, because nothing
recorded either. `estimate_cost_usd` was the only function in the repo that
produced a dollar figure, and it was computed, compared against the approval
threshold, and thrown away — surviving only inside the exception raised when the
gate refused. `batch_fetch`'s `elapsed_secs` was the only clock, and it was
batch-wide.

So: one append per retrieval, at the moment it happens, to
`data/runs/<batch>.jsonl`. Written as the run proceeds rather than at the end,
so a batch that dies in stage 3 still leaves its accounting behind.

Three decisions worth not re-litigating.

**`append` never raises.** This is the only thing in this repo whose default is
the opposite of every gate, and the exception is the point: an observer that can
halt the thing it observes is worse than no observer. A ledger write failing
must not be able to kill a batch that was otherwise going to ship.

**A missing ledger is exit 2, not zero.** Same asymmetry as the dedupe wall. A
missing wall must never read as "nobody has been contacted"; a missing ledger
must never read as "this batch cost nothing".

**`purpose` is what makes the retrieve-once invariant checkable.** The rule the
proposal argues for is that information is retrieved exactly once per (lead,
source), and the only permitted second fetch is a verification — which must be a
live fetch, because a verifier reading a cache is certifying the cache. So a
second record for the same `(lead_key, url)` that is not `purpose="verify"` is a
duplicate, and `summarise` names it. **It does not fail on one.** Making the
invariant blocking belongs with the stage that removes the duplicate; a gate
that can halt a real send file over an accounting line is a gate people learn to
route around.

The costs here are Apify's own **estimates**, not billed amounts. The runner
uses `run-sync-get-dataset-items`, which collapses a run to its output, so
`usageTotalUsd` is never fetched. A ledger that implied otherwise would be worse
than none.
"""

from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass, asdict, fields as dataclass_fields
from datetime import date, datetime, timezone
from pathlib import Path

RUNS_DIR = "data/runs"

PURPOSES = ("observe", "verify")
OUTCOMES = ("ok", "empty", "error", "blocked")

# The free rungs record themselves through the CLI, on trust: an agent's own
# WebSearch and WebFetch happen model-side and are invisible to Python. Keeping
# them distinguishable in `retrieved_by` is what stops the ledger from claiming
# an authority over tier 1 it does not have.
REPORTED_BY = ("websearch", "webfetch")

# Two things live in this file. A line with no `kind` is a Retrieval, which is
# every line written before 2026-08-01 and every line Python writes itself.
PASS_KIND = "pass"

_lock = threading.Lock()

# Process-scoped. One CLI invocation is one retrieval context — this is a
# command, not a server. `audit/apify.py` knows the technical facts of a fetch
# (which actor, which URL, how long, what it was priced at); only the caller
# knows the run facts (which lead, which stage, observe or verify).
_context: dict[str, str] = {}


class LedgerUnreadable(RuntimeError):
    """The ledger could not be read. Always exit 2, never an empty report."""


@dataclass
class Retrieval:
    """One fetch. The unit is (lead, source), not lead."""

    lead_key: str = ""
    stage: str = ""              # fetch | resolve | research | hook | verify | email
    platform: str = ""           # site | linkedin | instagram | youtube | linkinbio | web | email
    url: str = ""
    retrieved_by: str = ""       # tier0 | websearch | webfetch | apify:<actor_key>
    cost_usd: float | None = 0.0  # None when the actor could not be priced
    secs: float = 0.0
    outcome: str = "ok"          # ok | empty | error | blocked
    purpose: str = "observe"     # observe | verify
    at: str = ""                 # ISO timestamp, stamped by append()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Retrieval":
        known = cls.__dataclass_fields__
        return cls(**{k: v for k, v in data.items() if k in known})


# ------------------------------------------------------------------- context


def set_context(**values: str) -> None:
    """Set the run facts for this process. Blank values are ignored, so a
    command that has no lead does not blank one an earlier call set."""
    for key, value in values.items():
        if value:
            _context[key] = str(value)


def get_context() -> dict:
    return dict(_context)


def clear_context() -> None:
    _context.clear()


# --------------------------------------------------------------------- paths


# Where a subagent can find the label without being told it. `work/` is
# gitignored and per-container, which is exactly the lifetime of a batch.
BATCH_FILE = "work/BATCH"


def _batch_file(root: str | Path | None = None) -> Path:
    base = Path(root or os.environ.get("OUTBOUND_LEDGER_ROOT")
                or Path(__file__).resolve().parent.parent)
    return base / BATCH_FILE


def batch_source(batch: str | None = None,
                 root: str | Path | None = None) -> tuple:
    """The label and where it came from, in resolution order.

    The second half exists because of how the label was lost. Twelve workers
    were told to pass `--batch` on every `apify` call; the flag did not exist,
    one of the twelve checked and said so, and 15 retrievals — five of them paid
    hook rungs — landed in the wrong file. `ledger report` then under-reported
    the batch by 30% and the wrong number was quoted before anyone noticed.

    A shell's `OUTBOUND_BATCH` does not reach a subagent: it is a different
    process, started from a different environment. A file does. So the label
    stops being something an orchestrator remembers to say and becomes something
    any process can look up — and `ledger batch` with no argument prints this
    tuple, so "which batch am I in" is answerable rather than assumed.
    """
    if batch:
        return batch, "passed in"
    if _context.get("batch"):
        return _context["batch"], "this process's ledger context"
    if os.environ.get("OUTBOUND_BATCH"):
        return os.environ["OUTBOUND_BATCH"], "OUTBOUND_BATCH"
    try:
        stored = _batch_file(root).read_text(encoding="utf-8").strip()
    except OSError:
        stored = ""
    if stored:
        return stored, BATCH_FILE
    # Never an error. A batch that has not named itself still gets a ledger,
    # because the alternative is a paid fetch whose accounting is dropped for
    # want of a label — and this module's one rule is that it cannot halt what
    # it observes.
    return date.today().isoformat(), "today, because nothing named a batch"


def batch_label(batch: str | None = None) -> str:
    """The batch this run belongs to. See `batch_source` for the order and why
    the file is in it."""
    return batch_source(batch)[0]


def set_batch(label: str, root: str | Path | None = None) -> Path:
    """Write the label where every later process can find it."""
    target = _batch_file(root)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(label.strip() + "\n", encoding="utf-8")
    return target


def path(batch: str | None = None, root: str | Path | None = None) -> Path:
    """Where this batch's ledger lives.

    `OUTBOUND_LEDGER_ROOT` redirects the whole thing, which is what the test
    suite uses — the same shape as `OUTBOUND_COPY_SOURCE=csv`. Without it a
    test that exercised `batch_fetch` would append real lines to the real
    repo's ledger, and the first honest cost figure this machine produces would
    have a test run mixed into it.
    """
    return artifact(".jsonl", batch=batch, root=root)


def artifact(suffix: str, *, batch: str | None = None,
             root: str | Path | None = None) -> Path:
    """Any per-batch file in `data/runs/` — the ledger, and everything beside it.

    `select`, `metrics` and `replies` each write one, and each had built the
    path itself from a literal `"data/runs/"`. Three copies of a directory name
    is the drift D23 exists about, and it had a second cost: none of the three
    honoured `OUTBOUND_LEDGER_ROOT`, so a test of any of them wrote into the
    real repo's run directory beside real batches.

    `suffix` starts with `-` for a sibling (`-select.json`) or `.` for the
    ledger itself.
    """
    base = Path(root or os.environ.get("OUTBOUND_LEDGER_ROOT")
                or Path(__file__).resolve().parent.parent)
    return base / RUNS_DIR / f"{batch_label(batch)}{suffix}"


# --------------------------------------------------------------------- write


def append(record: Retrieval, *, batch: str | None = None,
           root: str | Path | None = None) -> bool:
    """Append one retrieval. Returns whether it was written; NEVER raises.

    Every other check in this repo fails closed. This one fails open, on
    purpose — see the module docstring. The return value exists so a test can
    assert the difference between "wrote it" and "swallowed it", which is the
    only way a silent no-op stays honest.
    """
    try:
        if not record.at:
            record.at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        line = json.dumps(record.to_dict(), ensure_ascii=False, default=str)
        target = path(batch, root)
        with _lock:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
        return True
    except Exception:
        return False


def record_pass(*, stage: str, agent: str = "", model: str = "", count: int = 1,
                batch: str | None = None, root: str | Path | None = None) -> bool:
    """Record agent passes, on trust. Never raises, same as `append`.

    **This is the Claude bill, and nothing in this repo could see it.** The
    Apify ledger exists because every cost claim about retrieval had been
    reconstructed by hand from a journal entry. The model side was in exactly
    that state one layer up: `2026-08-01-q1` cost about 64 agent passes for 20
    leads and 5 shipped rows, and the only record of it was a number an
    orchestrator typed into `metrics --passes` at the end of a long session —
    one scalar, no stage, no model. "The drafting loop is most of the bill" was
    a guess nobody could check.

    Reported on trust, exactly like `ledger add`: an agent pass happens in the
    main loop and Python cannot see one. `kind` keeps these separable from
    retrievals so a pass can never be counted as a fetch.

    **Counts, not dollars.** Model prices are a value this repo does not own,
    and the standing rule is that a doc names the authority rather than copying
    it. A rate table here would be a number going stale in a file nobody
    remembers to update, printed with two decimal places.
    """
    return append_raw({
        "kind": PASS_KIND, "stage": stage, "agent": agent, "model": model,
        "count": max(1, int(count or 1)),
    }, batch=batch, root=root)


def append_raw(payload: dict, *, batch: str | None = None,
               root: str | Path | None = None) -> bool:
    """One JSON line, stamped. Never raises — the ledger's rule, unchanged."""
    try:
        line = dict(payload)
        line.setdefault(
            "at", datetime.now(timezone.utc).isoformat(timespec="seconds"))
        target = path(batch, root)
        with _lock:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(line, ensure_ascii=False,
                                        default=str) + "\n")
        return True
    except Exception:
        return False


def record(*, batch: str | None = None, root: str | Path | None = None,
           **values) -> bool:
    """Build a Retrieval from the ambient context plus what the caller knows,
    and append it. The caller's values win — the context is a default, not an
    override, or a stage label set once would outrank the truth."""
    known = {f.name for f in dataclass_fields(Retrieval)}
    fields = {k: v for k, v in get_context().items() if k in known}
    fields.update({k: v for k, v in values.items() if k in known})
    return append(Retrieval(**fields), batch=batch, root=root)


# ---------------------------------------------------------------------- read


def read(batch: str | None = None,
         root: str | Path | None = None) -> tuple[list[Retrieval], int]:
    """(records, malformed line count). Raises LedgerUnreadable on a missing
    or unopenable file.

    A malformed line is skipped and counted rather than fatal: the ledger is
    appended to as a run proceeds, so a batch killed mid-write legitimately
    leaves a half-written last line. Losing the other 400 records to it would
    defeat the reason for writing them as we go.
    """
    target = path(batch, root)
    if not target.is_file():
        raise LedgerUnreadable(
            f"no ledger at {target} — a missing ledger is not a zero-cost batch")
    try:
        text = target.read_text(encoding="utf-8")
    except OSError as exc:
        raise LedgerUnreadable(f"cannot read {target}: {type(exc).__name__}") from exc

    records, malformed = [], 0
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except ValueError:
            malformed += 1
            continue
        if not isinstance(data, dict):
            malformed += 1
        elif data.get("kind") == PASS_KIND:
            # A pass is not a retrieval and must never be counted as one. It
            # has no url, so `duplicates` would skip it — but `summarise` would
            # add it to the fetch count and report agent passes as free fetches.
            continue
        else:
            records.append(Retrieval.from_dict(data))
    return records, malformed


def read_passes(batch: str | None = None,
                root: str | Path | None = None) -> list[dict]:
    """The reported agent passes for a batch. Empty is a real answer.

    Separate from `read` rather than a second return value, so every existing
    caller keeps meaning what it meant. Raises `LedgerUnreadable` on a missing
    file for the same reason `read` does: a missing ledger is not a batch that
    cost nothing.
    """
    target = path(batch, root)
    if not target.is_file():
        raise LedgerUnreadable(
            f"no ledger at {target} — a missing ledger is not a zero-cost batch")
    out = []
    for line in target.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except ValueError:
            continue
        if isinstance(data, dict) and data.get("kind") == PASS_KIND:
            out.append(data)
    return out


def passes_by(entries: list, key: str) -> dict:
    """Reported passes totalled by one field, largest first.

    `?` is not this function's business — an empty dict means nothing was
    reported, and `metrics` is where that becomes a `?` rather than a 0.
    """
    totals: dict = {}
    for entry in entries or []:
        name = str(entry.get(key) or "").strip() or "unnamed"
        totals[name] = totals.get(name, 0) + int(entry.get("count") or 1)
    return dict(sorted(totals.items(), key=lambda kv: (-kv[1], kv[0])))


# ------------------------------------------------------------------ analysis


def duplicates(records: list[Retrieval]) -> list[dict]:
    """Second and later fetches of the same (lead, url) that are not a verify.

    The invariant, stated once: information is retrieved exactly once per lead
    per source, and the only permitted second fetch is a verification. A
    verifier's fetch is not overhead, it is the product — it is the one thing in
    this system that has actually caught a fabricated claim — so it is exempt
    here rather than merely tolerated.
    """
    seen: dict[tuple[str, str], Retrieval] = {}
    out = []
    for entry in sorted(records, key=lambda r: r.at):
        if not entry.url:
            continue
        key = (entry.lead_key, entry.url)
        first = seen.get(key)
        if first is None:
            seen[key] = entry
            continue
        if entry.purpose == "verify":
            continue
        out.append({
            "lead_key": entry.lead_key,
            "url": entry.url,
            "first": f"{first.stage or '?'} via {first.retrieved_by or '?'}",
            "again": f"{entry.stage or '?'} via {entry.retrieved_by or '?'}",
            "cost_usd": entry.cost_usd or 0.0,
        })
    return out


def _total(records: list[Retrieval]) -> float:
    return round(sum(r.cost_usd or 0.0 for r in records), 4)


def summarise(records: list[Retrieval]) -> dict:
    """Totals, breakdowns, per-lead cost, and the duplicate fetches."""
    by_source: dict[str, dict] = {}
    by_stage: dict[str, dict] = {}
    by_lead: dict[str, dict] = {}
    for entry in records:
        for bucket, key in ((by_source, entry.retrieved_by or "?"),
                            (by_stage, entry.stage or "?"),
                            (by_lead, entry.lead_key or "?")):
            slot = bucket.setdefault(key, {"n": 0, "cost_usd": 0.0, "secs": 0.0})
            slot["n"] += 1
            slot["cost_usd"] = round(slot["cost_usd"] + (entry.cost_usd or 0.0), 4)
            slot["secs"] = round(slot["secs"] + (entry.secs or 0.0), 1)

    unpriced = [r for r in records if r.cost_usd is None]
    return {
        "count": len(records),
        "cost_usd": _total(records),
        "secs": round(sum(r.secs or 0.0 for r in records), 1),
        "leads": len({r.lead_key for r in records if r.lead_key}),
        "unpriced": len(unpriced),
        "blocked": sum(1 for r in records if r.outcome == "blocked"),
        "errors": sum(1 for r in records if r.outcome == "error"),
        "by_source": by_source,
        "by_stage": by_stage,
        "by_lead": by_lead,
        "duplicates": duplicates(records),
    }


def report(records: list[Retrieval], *, batch: str | None = None,
           malformed: int = 0, leads: int = 0, verbose: bool = False) -> str:
    """The block a skill quotes. `leads` is the batch's real lead count when the
    caller knows it, so cost-per-lead is not silently computed over only the
    leads that happened to need a fetch.

    `verbose` prints every duplicate pair; the default groups them by shape,
    which is the form the answer actually takes."""
    stats = summarise(records)
    denominator = leads or stats["leads"]
    per_lead = (stats["cost_usd"] / denominator) if denominator else 0.0

    lines = [
        f"LEDGER {batch_label(batch)}: {stats['count']} retrieval(s), "
        f"${stats['cost_usd']:.4f} est over {stats['leads']} lead(s), "
        f"{stats['secs']:.0f}s",
        f"  ${per_lead:.4f}/lead"
        + (f" over {denominator} lead(s)" if denominator else ""),
    ]
    for source, slot in sorted(stats["by_source"].items()):
        lines.append(f"  {source:24} {slot['n']:4} call(s)  "
                     f"${slot['cost_usd']:.4f}  {slot['secs']:.0f}s")
    if stats["by_stage"]:
        lines.append("  by stage: " + ", ".join(
            f"{stage} {slot['n']}" for stage, slot in sorted(stats["by_stage"].items())))
    if stats["unpriced"]:
        lines.append(f"  {stats['unpriced']} run(s) could not be priced — "
                     f"compute-billed actors are not a lookup failure")
    if stats["blocked"]:
        lines.append(f"  {stats['blocked']} run(s) BLOCKED by the cost gate")
    if stats["errors"]:
        lines.append(f"  {stats['errors']} retrieval(s) errored")
    if stats["duplicates"] and not verbose:
        # Grouped, because the pattern is the finding and the list is not.
        # `2026-08-02-q3` had 129 duplicate pairs and its own journal entry
        # names the answer in one sentence — "110 of this batch's 129 duplicate
        # pairs are that" — which is a shape, arrived at by reading 129 lines
        # that were identical except for a name. The orchestrator keeps every
        # one of those lines for the rest of the run.
        shapes: dict = {}
        for dupe in stats["duplicates"]:
            key = f"{dupe['first']} then {dupe['again']}"
            shapes.setdefault(key, []).append(dupe["lead_key"] or "?")
        for shape, leads in sorted(shapes.items(), key=lambda kv: -len(kv[1])):
            shown = ", ".join(sorted(set(leads))[:3])
            more = len(set(leads)) - 3
            lines.append(f"  DUPLICATE  {len(leads)}x  {shape}"
                         f"  [{shown}{f' +{more} more' if more > 0 else ''}]")
        lines.append(f"  {len(stats['duplicates'])} duplicate pair(s) in "
                     f"{len(shapes)} shape(s) — `--verbose` for every pair")
    elif stats["duplicates"]:
        for dupe in stats["duplicates"]:
            lines.append(f"  DUPLICATE  {dupe['lead_key'] or '?'}  {dupe['url']}  "
                         f"{dupe['first']} then {dupe['again']}")
    if not stats["duplicates"]:
        lines.append("  no duplicate fetch: every (lead, url) retrieved once, "
                     "or again only to verify")
    if malformed:
        lines.append(f"  {malformed} unreadable line(s) skipped — a run that "
                     f"died mid-write leaves one")
    return "\n".join(lines)
